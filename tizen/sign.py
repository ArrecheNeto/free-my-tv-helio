#!/usr/bin/env python3
"""Signs TelaLivre.wgt for Samsung TVs from 2016 to 2022 (Tizen 2.4 to 6.5), without Tizen Studio.

    python3 tizen/sign.py          # the certificate password comes from FMTV_CERT_PASS, or is asked for

It writes the two signatures Tizen Studio's `tizen package` writes: author-signature.xml (an author certificate issued
by the Tizen Developers CA, as `tizen certificate` makes it) and signature1.xml (Tizen's public SDK distributor). Both
CAs come from Samsung's certificate-generator package on download.tizen.org. The author certificate is made once and
kept in ~/.freemytv-tizen: updates must be signed with the same one, or the TV refuses them.
Needs the `cryptography` package (pip install cryptography).
"""
import base64
import datetime
import getpass
import hashlib
import io
import os
import sys
import urllib.parse
import urllib.request
import zipfile

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa
from cryptography.hazmat.primitives.serialization import pkcs12
from cryptography.x509.oid import ExtendedKeyUsageOID, NameOID

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WGT = os.path.join(ROOT, 'TelaLivre.wgt')
HOME = os.path.join(os.path.expanduser('~'), '.freemytv-tizen')
CERTS = os.path.join(HOME, 'certs')
AUTHOR_KEY = os.path.join(HOME, 'author-key.pem')
AUTHOR_CERT = os.path.join(HOME, 'author-cert.pem')
GENERATOR = ('https://download.tizen.org/sdk/tizenstudio/official/binary/'
             'certificate-generator_0.1.4_ubuntu-64.zip')
PREFIX = 'data/tools/certificate-generator/certificates/'

DSIG = 'http://www.w3.org/2000/09/xmldsig#'
# Digests of the fixed <Object Id="prop"> each signature carries (the same in every Tizen package).
PROP = {
    'AuthorSignature': 'aXbSAVgmAz0GsBUeZ1UmNDRrxkWhDUVGb45dZcNRq429wX3X+x6kaXT3NdNDTSNVTU+ypkysPMGvQY10fG1EWQ==',
    'DistributorSignature': '/r5npk2VVA46QFJnejgONBEh4BWtjrtu9x/IFeLksjWyGmB/cMWKSJWQl7aU3YRQRZ3AesG8gF7qGyvKX9Snig==',
}


def wrap(b64):
    return '\n'.join(b64[i:i + 76] for i in range(0, len(b64), 76))


def fetch_certs():
    if os.path.exists(os.path.join(CERTS, 'developer', 'tizen-developer-ca.cer')):
        return
    print('Baixando os certificados da Tizen (download.tizen.org)...')
    data = urllib.request.urlopen(GENERATOR, timeout=120).read()
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        for name in z.namelist():
            if name.startswith(PREFIX) and not name.endswith('/'):
                target = os.path.join(CERTS, *name[len(PREFIX):].split('/'))
                os.makedirs(os.path.dirname(target), exist_ok=True)
                with open(target, 'wb') as f:
                    f.write(z.read(name))


def load_cert(path):
    with open(path, 'rb') as f:
        data = f.read()
    return x509.load_pem_x509_certificate(data) if b'-----BEGIN' in data else x509.load_der_x509_certificate(data)


def make_author(password):
    ca_cert = load_cert(os.path.join(CERTS, 'developer', 'tizen-developer-ca.cer'))
    with open(os.path.join(CERTS, 'developer', 'tizen-developer-ca-privatekey.pem'), 'rb') as f:
        ca_key = serialization.load_pem_private_key(f.read(), b'tizencertificatefordevelopercaroqkfwk')
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    now = datetime.datetime.now(datetime.timezone.utc)
    cert = (x509.CertificateBuilder()
            .subject_name(x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, 'Free My TV'),
                                     x509.NameAttribute(NameOID.COUNTRY_NAME, 'BR')]))
            .issuer_name(ca_cert.subject)
            .public_key(key.public_key())
            .serial_number(x509.random_serial_number())
            .not_valid_before(now - datetime.timedelta(days=1))
            .not_valid_after(now + datetime.timedelta(days=365 * 15))
            .add_extension(x509.BasicConstraints(ca=False, path_length=None), critical=False)
            .add_extension(x509.ExtendedKeyUsage([ExtendedKeyUsageOID.CODE_SIGNING]), critical=False)
            .sign(ca_key, hashes.SHA256()))
    os.makedirs(HOME, exist_ok=True)
    with open(AUTHOR_KEY, 'wb') as f:
        f.write(key.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8,
                                  serialization.BestAvailableEncryption(password.encode('utf-8'))))
    with open(AUTHOR_CERT, 'wb') as f:
        f.write(cert.public_bytes(serialization.Encoding.PEM) + ca_cert.public_bytes(serialization.Encoding.PEM))
    print('Certificado de autor criado em ' + HOME)


def author(password):
    with open(AUTHOR_KEY, 'rb') as f:
        try:
            key = serialization.load_pem_private_key(f.read(), password.encode('utf-8'))
        except ValueError:
            sys.exit('Senha errada (use a mesma da primeira vez).')
    with open(AUTHOR_CERT, 'rb') as f:
        chain = x509.load_pem_x509_certificates(f.read())
    return key, chain


def distributor():
    with open(os.path.join(CERTS, 'distributor', 'sdk-public', 'tizen-distributor-signer.p12'), 'rb') as f:
        key, cert, extra = pkcs12.load_key_and_certificates(f.read(), b'tizenpkcs12passfordsigner')
    return key, [cert] + list(extra or [])


def reference(uri, digest):
    transform = ('<Transforms>\n<Transform Algorithm="http://www.w3.org/2006/12/xml-c14n11"></Transform>\n'
                 '</Transforms>\n') if uri == '#prop' else ''
    return ('<Reference URI="%s">\n%s<DigestMethod Algorithm="http://www.w3.org/2001/04/xmlenc#sha512">'
            '</DigestMethod>\n<DigestValue>%s</DigestValue>\n</Reference>\n' % (uri, transform, wrap(digest)))


def signature(sig_id, files, key, chain):
    """files: [(uri, bytes)]; returns the signature file's XML."""
    refs = ''.join(reference(uri, base64.b64encode(hashlib.sha512(data).digest()).decode()) for uri, data in files)
    refs += reference('#prop', PROP[sig_id])
    signed_info = ('<SignedInfo>\n'
                   '<CanonicalizationMethod Algorithm="http://www.w3.org/2001/10/xml-exc-c14n#">'
                   '</CanonicalizationMethod>\n'
                   '<SignatureMethod Algorithm="http://www.w3.org/2001/04/xmldsig-more#rsa-sha512">'
                   '</SignatureMethod>\n' + refs + '</SignedInfo>\n')
    # Exclusive C14N of SignedInfo: already canonical, plus the default namespace it inherits.
    canonical = signed_info[:-1].replace('<SignedInfo>', '<SignedInfo xmlns="%s">' % DSIG, 1)
    value = key.sign(canonical.encode('utf-8'), padding.PKCS1v15(), hashes.SHA512())
    certs = ''.join('\n<X509Certificate>\n%s\n</X509Certificate>' % wrap(
        base64.b64encode(c.public_bytes(serialization.Encoding.DER)).decode()) for c in chain)
    role = 'author' if sig_id == 'AuthorSignature' else 'distributor'
    return ('<Signature xmlns="%s" Id="%s">\n' % (DSIG, sig_id) + signed_info +
            '<SignatureValue>\n%s\n</SignatureValue>\n' % wrap(base64.b64encode(value).decode()) +
            '<KeyInfo>\n<X509Data>' + certs + '\n</X509Data>\n</KeyInfo>\n'
            '<Object Id="prop"><SignatureProperties xmlns:dsp="http://www.w3.org/2009/xmldsig-properties">'
            '<SignatureProperty Id="profile" Target="#%s"><dsp:Profile URI="http://www.w3.org/ns/widgets-digsig#profile">'
            '</dsp:Profile></SignatureProperty>'
            '<SignatureProperty Id="role" Target="#%s"><dsp:Role URI="http://www.w3.org/ns/widgets-digsig#role-%s">'
            '</dsp:Role></SignatureProperty>'
            '<SignatureProperty Id="identifier" Target="#%s"><dsp:Identifier></dsp:Identifier></SignatureProperty>'
            '</SignatureProperties></Object>\n</Signature>\n' % (sig_id, sig_id, role, sig_id))


def main():
    if not os.path.exists(WGT):
        sys.exit('Gere o pacote antes: python tizen/build.py')
    password = os.environ.get('FMTV_CERT_PASS') or getpass.getpass('Senha do certificado: ')
    fetch_certs()
    if not os.path.exists(AUTHOR_KEY):
        make_author(password)
    a_key, a_chain = author(password)
    d_key, d_chain = distributor()

    with zipfile.ZipFile(WGT) as z:
        files = [(urllib.parse.quote(n, safe='/'), z.read(n)) for n in sorted(z.namelist())
                 if not n.endswith('/') and n != 'author-signature.xml'
                 and not (n.startswith('signature') and n.endswith('.xml'))]
    author_xml = signature('AuthorSignature', files, a_key, a_chain).encode('utf-8')
    files = [('author-signature.xml', author_xml)] + files
    dist_xml = signature('DistributorSignature', files, d_key, d_chain).encode('utf-8')

    tmp = WGT + '.tmp'
    with zipfile.ZipFile(tmp, 'w', zipfile.ZIP_DEFLATED) as z:
        z.writestr('signature1.xml', dist_xml)
        for uri, data in files:
            z.writestr(urllib.parse.unquote(uri), data)
    os.replace(tmp, WGT)
    print('Assinado: ' + WGT)


if __name__ == '__main__':
    main()
