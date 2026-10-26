# Free My TV na sua Samsung (versão com visual quente)

Uma tela inicial sem anúncios para TVs Samsung, com um visual novo: creme de dia, grafite quente de noite,
destaque terracota e títulos em serifa. Seus apps numa fileira, clima, relógio e, se quiser, os filmes e séries
em alta dos apps que você já tem.

É uma versão do [Free My TV](https://github.com/simbasjungles/free-my-tv) (licença MIT), com o visual redesenhado
e um instalador de dois cliques para Windows. Não precisa de Tizen Studio nem de conta Samsung.

## Funciona em

TVs Samsung de **2016 a 2022** (Tizen 2.4 a 6.5). Para descobrir o ano, veja a letra depois do tamanho no modelo:
K = 2016, M = 2017, N = 2018, R = 2019, T = 2020, A = 2021, B = 2022. Exemplo: UN65**T**U8000 é de 2020.

TVs de 2023 em diante pedem um certificado da conta Samsung, que este instalador ainda não faz.

## Você vai precisar

- Um PC com Windows na mesma rede Wi-Fi da TV
- Python 3 (python.org; na instalação, marque "Add Python to PATH")

## Passo a passo

**1. Descubra o IP do seu PC.** Tecle Windows + R, digite `cmd`, Enter, e depois `ipconfig`. Anote o
"Endereço IPv4" do adaptador que tem "Gateway Padrão" preenchido (algo como 192.168.0.15).

**2. Ligue o modo desenvolvedor na TV.**
- Abra **Apps** na TV e digite **1 2 3 4 5**
- Se nada acontecer: use o teclado numérico do app **SmartThings** no celular, ou um teclado USB na TV
- Ligue **Developer mode**, coloque o IP do PC em **Host PC IP**, dê OK
- Reinicie a TV (tire da tomada por uns 5 segundos)

**3. Descubra o IP da TV.** Configurações > Geral > Rede > Status da rede > Configurações de IP.

**4. Baixe este projeto** (botão verde **Code > Download ZIP**) e descompacte.

**5. Dê dois cliques em `instalar.bat`.** Se o Windows avisar, clique em **Mais informações > Executar assim mesmo**.
Ele pede o IP da TV, prepara tudo, pede para você criar uma senha (guarde: as atualizações usam a mesma) e manda o
app para a TV.

**6. Para a TV já ligar no Free My TV:** nas configurações da TV, em Opções da Tela Inicial, ligue
**Autorun Last App**.

## Opcional: sua cidade e os filmes em alta

Sem configurar nada, a cidade do clima vem do fuso horário da TV. Para escolher a sua cidade e ter os destaques de
filmes e séries, copie `config.example.properties` para `config.properties`, preencha `latitude`, `longitude`,
`city` e sua chave gratuita do TMDB em `tmdb_key` (themoviedb.org > Configurações > API), e rode `instalar.bat` de
novo. A chave é sua: ela fica só no seu PC e na sua TV.

## Para remover

Na TV: Apps > Configurações > Free My TV > Excluir. A tela inicial da Samsung nunca é alterada.

## Créditos

- [Free My TV](https://github.com/simbasjungles/free-my-tv), de simbasjungles (MIT): o app original
- Fonte [Source Serif 4](https://github.com/adobe-fonts/source-serif) (SIL OFL)
- Visual e instalador para Windows desta versão: Helio Arreche, com Claude
