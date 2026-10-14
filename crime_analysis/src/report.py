from pathlib import Path
import pandas as pd,numpy as np,json,html
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Table,TableStyle,PageBreak,Image,KeepTogether
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet,ParagraphStyle
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
O=Path('investigation/results');out=Path('investigation');styles=getSampleStyleSheet();styles.add(ParagraphStyle(name='BodyPT',fontName='Helvetica',fontSize=10,leading=14,spaceAfter=8));styles['Heading1'].fontSize=17;styles['Heading1'].leading=21;styles['Heading1'].textColor=colors.HexColor('#174762');styles['Heading2'].fontSize=12;styles['Heading2'].spaceBefore=10
story=[];md=[]
def h(t):story.append(Paragraph(t,styles['Heading1']));md.append('\n# '+t+'\n')
def sub(t):story.append(Paragraph(t,styles['Heading2']));md.append('\n## '+t+'\n')
def p(t):story.append(Paragraph(t,styles['BodyPT']));md.append(t.replace('<b>','').replace('</b>','')+'\n')
def table(headers,rows,widths=None):
 data=[[Paragraph(html.escape(str(v)),ParagraphStyle('t',fontSize=8,leading=10,textColor=colors.white if i==0 else colors.black)) for v in row] for i,row in enumerate([headers]+rows)]
 t=Table(data,colWidths=widths,repeatRows=1,hAlign='LEFT');t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#174762')),('VALIGN',(0,0),(-1,-1),'TOP'),('BOTTOMPADDING',(0,0),(-1,-1),6),('TOPPADDING',(0,0),(-1,-1),6),('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.HexColor('#f0f4f7'),colors.white]),('LINEBELOW',(0,0),(-1,0),.5,colors.gray)]));story.append(t);story.append(Spacer(1,9));md.append('| '+' | '.join(headers)+' |\n| '+' | '.join(['---']*len(headers))+' |\n'+'\n'.join('| '+' | '.join(map(str,r))+' |' for r in rows))
def page():story.append(PageBreak())
def img(name,w=495):
 from PIL import Image as PI
 path=O/name;im=PI.open(path);story.append(Image(str(path),width=w,height=w*im.height/im.width));md.append('!['+name+'](results/'+name+')\n')
def fmt(x,k=3):return f'{x:,.{k}f}'.replace(',','X').replace('.',',').replace('X','.')
models=pd.read_csv(O/'models.csv').set_index('model');co=pd.read_csv(O/'coefficients.csv');sel=pd.read_csv(O/'selections.csv').set_index('sample');cv=pd.read_csv(O/'cv.csv');sp=pd.read_csv(O/'spatial_cv.csv')
# PAGE 1
h('Vegetação, sombra e crimes de veículos: auditoria da seleção espacial')
p('Nota técnica para discussão com o Prof. Dr. Luis Gustavo Nonato • Pesquisa de Normando Codá Amazonas • 23 de setembro de 2026')
sub('Resposta à pergunta central')
p('<b>A grade de 45.004 células permite investigar associações condicionais nas células que intersectam a rede viária fornecida e possuem os dez controles completos.</b> Ela não representa, sem restrições, toda a superfície dos 26 distritos. A seleção viária já ocorreu implicitamente: nenhuma das 45.004 células está sem interseção linear positiva com a rede.')
p('Uma seleção mais estrita por classes viárias ou comprimento mínimo muda a população, mas, nas sensibilidades executadas, altera pouco os coeficientes ambientais. Incorporar comprimento e composição viária como covariáveis altera mais a magnitude dos coeficientes e melhora modestamente a previsão. Isso não transforma o estudo em uma análise de risco por veículo nem resolve a dependência espacial.')
sub('O que foi confirmado computacionalmente')
p('A base maior contém 64.837 células. Delas, 46.215 intersectam vias; 18.622 não intersectam. A remoção dos casos com algum controle ausente deixa exatamente 45.004 células. Os atributos compartilhados com a base completa são idênticos. Poisson, NB2 simples, NB2 completa e Moran residual reproduzem os números históricos.')
sub('O que permanece exploratório')
p('As associações ajustadas por proxies viárias, os intervalos por blocos espaciais e a comparação preditiva não constituem evidência causal. A vegetação tem associação negativa pequena e sensível à escala de agrupamento dos erros; a sombra mantém associação positiva. Não foi validada heterogeneidade local dos coeficientes.')
sub('Limite que impede uma conclusão mais ampla')
p('Não há camada efetiva de uso do solo nos anexos disponíveis: os dois arquivos chamados landuse são redes de linhas. A classificação ambiental não ficou acessível e o raster citado pelo projeto QGIS não foi fornecido. Portanto, não é possível quantificar parques, prédios, estacionamentos ou ocupações dentro de cada célula. A análise A com controles reais de uso do solo permanece não executável; a comparação viária B/C foi realizada.')
# PAGE 2
page();h('1. Estrutura, qualidade e origem das células')
table(['Arquivo/camada','Feições','Conteúdo confirmado'],[['grid_50_analysis_controls_v2','64.837','Polígonos de células; dois desfechos; controles com ausências'],['grid_50_model_complete_cases_v2','45.004','Subconjunto exato dos casos completos'],['grid_cells_without_street','18.622','Complemento sem via; inclui residencia_n apenas aqui'],['landuse_grid50_final','40.162','MultiLineString; atributos e seis classes viárias'],['landuse / recortado','41.177','MultiLineString; mesma cobertura de células com via'],['fase9.qgz','5 referências','Projeto, sem incorporar raster ou camada ambiental']], [180,55,260])
p('Todas as camadas vetoriais fornecidas declaram EPSG:31983. Não foram encontradas geometrias inválidas nem duplicatas geométricas exatas. Os identificadores de célula são únicos. Áreas geométricas variam de 2.499,9957 a 2.500 m²; cell_area vale 2.500 em todas. A diferença máxima de 0,0043 m² é desprezível para esta escala.')
p('A base maior cobre 162,0925 km² de células; a completa, 112,51 km². Esses números são áreas dos polígonos fornecidos, não áreas oficiais dos distritos. Faltam os limites administrativos e o procedimento original de recorte, de modo que a cobertura exata dos 26 distritos e a origem das 64.837 células não podem ser certificadas.')
p('A igualdade entre casos completos e dropna dos dez controles reconstrói a regra final de seleção; não comprova o histórico exato de processamento no QGIS. O notebook começa lendo uma base já pronta, com nome sem v2. O projeto contém caminhos e estilos, mas suas descrições de proveniência estão vazias.')
p('As contagens disponíveis são inteiras não negativas, embora gravadas como REAL. Vegetação e sombra permanecem em [0,100], e sua soma não excede 100. Há 407 áreas de vegetação e quatro de sombra ligeiramente acima de 2.500 m²; a discrepância máxima entre percentual armazenado e área/2.500 truncada em 100 é cerca de 0,0175 ponto percentual. É um alerta de cálculo/precisão, não evidência de grande erro ambiental. Preservaram-se os percentuais originais para reproduzir os modelos.')
p('residencia_n está ausente nas duas bases principais. No arquivo sem vias há somente um evento nessa variável; ele não permite reconstruir a população nem ajustar o desfecho residencial. Os períodos exatos, a geocodificação e a deduplicação dos crimes não são auditáveis sem os pontos e metadados originais. Nomes de campos da rede mencionam 2022–2025, mas não demonstram a janela das contagens da grade.')
# PAGE 3
page();h('2. Dicionário e validade dos controles')
dictionary=[
 ['veiculo_n / celular_n','Contagem por célula; inteiros >=0','Categorias, período e processamento original não comprovados'],
 ['veg_pct / shadow_pct','Percentual da área da célula; 0–100','Imagem, data, acurácia e significado da sombra não auditáveis'],
 ['infrastructure_index','Real; 0–45,54','Fórmula, escala e componentes desconhecidos'],
 ['high_income','Binária 0/1','Limiar de renda, ano e suporte espacial desconhecidos'],
 ['streetlight','Inteiro; 0–379','Possível iluminação na rede; não provada contagem dentro da célula'],
 ['schools_r500m','Inteiro; 0–21','Nome sugere escolas em 500 m; tipo de distância e fonte não comprovados'],
 ['transport_hubs_r500m','Inteiro; 0–119','Objeto contado e rede/raio não comprovados'],
 ['police_station_r500m','Inteiro; 0–5','Objeto, fonte, raio e ano não comprovados'],
 ['private_parking_r500m','Inteiro; 0–307','Não equivale a vagas ou veículos expostos'],
 ['paid_parking_distance','Real; 0–4.738,46','Nome sugere distância; metros e algoritmo não documentados'],
 ['moradores','Real; 10–1.500 na amostra','Não comprovada população residente dentro da célula'],
 ['distancia_marco_zero','Real; 0–12.130','Unidade/algoritmo não documentados; não converter em fato apenas pelo CRS'],
 ['road_m / motor_m (novas)','Metros calculados em EPSG:31983','União das linhas recortadas por célula; não veículos-tempo']]
table(['Variável','Tipo/unidade observável','Limitação operacional'],dictionary,[126,160,209])
p('Os dez controles existem também nas linhas da rede. Para cada variável, 100% dos valores não nulos das células estão no intervalo dos segmentos que as atravessam; correspondência exata com a média simples varia de 42% a 97%. Isso é compatível com transferência/agregação da rede, mas não identifica o algoritmo original. Não tratar moradores como denominador da célula nem usar streetlight como inventário pontual validado.')
p('Ausências na base maior: 18.622 para sete controles; 18.973 para infraestrutura/renda; 19.490 para moradores. O arquivo columns.csv detalha todas as colunas, e os arquivos distributions trazem min, quartis, média, dispersão e máximos. As distribuições são dos valores armazenados; não validam seus rótulos.')
p('O modelo mantém as unidades originais para comparação histórica; internamente padroniza as covariáveis para otimizar, reconvertendo os coeficientes. Na validação, médias e desvios são calculados só no treinamento. Não se impôs offset de moradores, área ou comprimento viário.')
pd.DataFrame(dictionary,columns=['variable','observed_definition','limitation']).to_csv(O/'variable_dictionary.csv',index=False)
# PAGE 4
page();h('3. Populações e zeros: o que a seleção modifica')
labels={'parent':'Grade maior','roads_all':'Todas com via','complete':'Casos completos','no_roads':'Sem via','roads_incomplete':'Com via, incompletas','motor_complete':'Classes motorizadas >0 m','motor10_complete':'Motorizadas >=10 m','motor25_complete':'Motorizadas >=25 m'}
rows=[]
for k,l in labels.items():
 r=sel.loc[k];rows.append([l,fmt(r.n,0),fmt(r.veiculo_n_sum,0),fmt(r.veiculo_n_zero_pct,2),fmt(r.veg_mean,2),fmt(r.shadow_mean,2)])
table(['População','N','Crimes','Zeros %','Veg. %','Sombra %'],rows,[164,58,61,66,70,76])
p('Todas as seleções são geométricas e independentes das ocorrências. Foram conservadas as células com zero. Comprimentos são medidos após unir os pedaços de linhas na célula, evitando somar duas vezes geometrias sobrepostas. As duas versões da rede produzem as mesmas 46.215 células com interseção positiva.')
p('A seleção estrita considera LOCAL, COLETORA, ARTERIAL e RODOVIA. VIA DE PEDESTRES e VTR não entram por si sós; VTR tem definição não documentada. As seis classes são indicadores da rede, não categorias de uso do solo. Exigir 10 ou 25 m reduz interseções muito curtas, mas esses limiares são sensibilidades geométricas, não limiares validados de exposição.')
p('As 1.211 células viárias excluídas por ausências têm vegetação média de 17,14%, contra 12,39% nos casos completos, e contêm 364 crimes de veículos. Portanto, a ausência de controles não é espacial/ambientalmente neutra. O contraste não prova a direção de um viés causal. Modelos simples com todas as células viárias permitem avaliar parte da sensibilidade sem inventar os controles faltantes.')
p('As 18.622 células sem linha viária contêm 595 crimes de veículos e 4.525 de celulares. Ausência de eixo cartográfico não demonstra ausência de veículos: podem existir interiores de quadras, acessos privados, garagens, estacionamentos ou deslocamentos de geocodificação. Não é possível distinguir essas explicações sem camadas e pontos adicionais.')
p('Células predominantemente vegetadas (>50%) são 6,67% da amostra completa e 10,97% das células sem via. Isso não identifica parques. A exclusão de interiores muito vegetados muda o domínio da pergunta: o estudo atual trata do ambiente das células cruzadas por vias, não de toda vegetação urbana.')
img('map_selection.png')
# PAGE 5
page();h('4. Reprodução e sensibilidade dos modelos')
p('Especificação: log(mu)=intercepto + vegetação + sombra + controles; NB2 com Var(Y)=mu+alpha*mu². O desfecho é a contagem observada na célula. AICs abaixo só devem ser comparados na mesma amostra; diferenças entre amostras não selecionam o melhor modelo.')
labels_m={'poisson_simple':'Poisson simples','nb_simple':'NB2 simples','nb_full':'NB2 +10 controles','nb_roads':'NB2 +10 +via','nb_roadsonly':'NB2 +via, sem 10','motor_full':'NB2 motorizadas','motor10_full':'NB2 >=10 m','motor25_full':'NB2 >=25 m'}
rows=[]
for k,l in labels_m.items():
 r=models.loc[k];q=co[(co.model==k)&(co.block_m==0)].set_index('variable');rows.append([l,fmt(r.n,0),fmt(r.AIC,2),fmt(r.alpha,3),fmt(q.loc['veg_pct','beta'],6),fmt(q.loc['shadow_pct','beta'],6)])
table(['Modelo','N','AIC','alpha','beta veg.','beta sombra'],rows,[137,54,84,50,85,85])
p('Os AIC históricos de veículos foram reproduzidos: 79.507,56; 60.786,32; 60.403,83. O Poisson prevê 72,16% de zeros, contra 82,87% observados; a NB2 completa prevê 83,05%. A dispersão Pearson do Poisson é 3,83; na NB2 completa ainda é 1,39. NB2 melhora fortemente o ajuste, sem demonstrar adequação integral ou independência espacial.')
p('Na base maior, a NB2 simples tem beta vegetação -0,004004; em todas as células com via, -0,002029; nos 45.004 casos completos, -0,002015. A grande mudança decorre de incluir células sem via, mais do que da remoção das 1.211 células incompletas nessa especificação simples. Isso não estima a associação ajustada na base maior.')
p('Adicionar log(1+metros de via) e cinco proporções de classes (LOCAL omitida como referência) muda beta vegetação para -0,003284 e beta sombra para +0,004508. Em razões condicionais por 10 pontos percentuais, são aproximadamente -3,23% e +4,61% na contagem esperada. No modelo anterior, eram -1,79% e +3,54%. Comprimento é apenas proxy de oportunidade espacial; não mede fluxo, estacionamento ou tempo de exposição.')
p('Para celulares, os AIC também reproduzem o notebook: Poisson 265.398,53; NB2 simples 114.022,89; NB2 completa 109.483,72. Na completa, beta vegetação=-0,001369 e beta sombra=+0,003758. O foco da decisão continua sendo veículos; não há base suficiente para residências.')
p('Correção computacional: o ajuste inicial com controles viários retornou alpha quase zero e Hessiana inválida apesar de sinalizar convergência. Essa solução foi descartada. Inicialização explícita a partir do Poisson, com alpha=5, recuperou a solução interior acima. Uma segunda inicialização (alpha=1) confirmou o mesmo ótimo; a matriz tem posto completo e o maior VIF é 2,33. Scripts, avisos e critérios estão no pacote.')
# PAGE 6
page();h('5. Incerteza e dependência espacial')
p('Os resíduos são de Pearson: (y-mu)/sqrt(mu+alpha*mu²). Foram usados pesos por distância entre centroides, sem autovizinhança e normalizados por linha. A vizinhança de 70,72 m aproxima Queen em células regulares, mas não é uma topologia viária. A de 100,01 m é sensibilidade. As 15 ilhas na primeira matriz permanecem com pesos zero.')
mr=pd.read_csv(O/'moran.csv');table(['Modelo','Raio (m)','Moran I','p permutação'],[[r.model,fmt(r.radius,2),fmt(r.I,6),fmt(r.p_two_sided,3)] for r in mr.itertuples()],[180,90,110,115])
p('O valor histórico I=0,0482 é reproduzido por 70,72 m: I=0,048167, p=0,001 (999 permutações, seed 42). Acrescentar controles viários produz I=0,052602. Melhor ajuste/predição não equivale a resíduos espacialmente independentes. As permutações de resíduos ajustados são diagnóstico aproximado, não teste exato de todo o modelo.')
p('Intervalos por agrupamento em blocos quadrados de 500 m, 1 km e 2 km permitem dependência interna ao bloco, mas pressupõem independência entre blocos. Não são uma correção espacial definitiva. A origem dos blocos é a malha UTM em múltiplos do tamanho; nenhuma escala foi escolhida pela significância.')
rows=[]
for model in ['nb_full','nb_roads']:
 for size in [500,1000,2000]:
  q=co[(co.model==model)&(co.block_m==size)].set_index('variable');v=q.loc['veg_pct'];ss=q.loc['shadow_pct'];rows.append([model,str(size),str(int(v.clusters)),f'[{fmt(v.lo,6)}; {fmt(v.hi,6)}]',f'[{fmt(ss.lo,6)}; {fmt(ss.hi,6)}]'])
table(['Modelo','Bloco m','Grupos','IC95% beta vegetação','IC95% beta sombra'],rows,[91,56,54,147,147])
p('A vegetação não tem evidência estável em todas as escalas. Mesmo com controles viários, o IC por blocos de 2 km inclui zero. A sombra tem sinal positivo nos intervalos examinados. Persistem confundimento, erro de mensuração e autocorrelação entre blocos; não se conclui proteção causal da vegetação nem mecanismo causal da sombra.')
# PAGE 7
page();h('6. Validação espacial e auditoria do piloto')
p('Cinco blocos KMeans nas coordenadas (seed 42, 20 inicializações), mantendo a geografia histórica. Em cada rodada, removem-se do treino células cujo centro está a até 300 m de qualquer centro de teste; a distância mínima efetiva é 304,14 m. Este buffer é entre centroides, não entre bordas dos polígonos. Todos os parâmetros e transformações são ajustados no treino. Não houve busca de hiperparâmetros.')
rows=[]
for k in range(5):
 q=cv[(cv.fold==k)&(cv.target=='all')].set_index('model');v=q.loc['global'];r=q.loc['road_adjusted'];rows.append([str(k),fmt(v.n_test,0),fmt(v.logscore,6),fmt(r.logscore,6),fmt(r.logscore-v.logscore,6)])
table(['Bloco','N teste','NB2 global','NB2 +via','Diferença'],rows,[65,80,117,117,116])
def weighted(d,col='n_test'):return np.average(d.logscore,weights=d[col])
global_cv=weighted(cv[(cv.model=='global')&(cv.target=='all')]);road_cv=weighted(cv[(cv.model=='road_adjusted')&(cv.target=='all')]);hist=weighted(sp[sp['mode']=='historical_fixed_centers'],'n');strict=weighted(sp[sp['mode']=='training_only_centers'],'n')
p(f'Log-score médio ponderado global: {fmt(global_cv,6)}; com controles viários: {fmt(road_cv,6)}; ganho: {fmt(road_cv-global_cv,6)} por célula. Houve melhora em quatro blocos e piora em um. Esse ganho modesto é maior que o do piloto espacial, mas não se atribui significância a cinco diferenças nem se declara validação externa definitiva. Para o mesmo alvo restrito >=25 m, a melhora é cerca de 0,00561 por célula; ambos os modelos foram treinados na população completa.')
p(f'O piloto com 40 bases gaussianas foi reexecutado: centros históricos definidos só por coordenadas, largura 1.500 m, exclusão dos centros distantes mais de 1.500 m do treino, residualização só no treino, sem padronização individual dos termos espaciais, penalidade 100 e alpha do modelo global do treino. Resultado {fmt(hist,6)}, ganho {fmt(hist-global_cv,6)}: próximo do relato -0,679797 e +0,000122. A pequena divergência é compatível com tolerância mais estrita e otimização. Todos os ajustes convergiram com predições finitas.')
p(f'Uma versão mais estrita, reconstruindo os 40 centros exclusivamente no treino, obteve {fmt(strict,6)}, ganho {fmt(strict-global_cv,6)}. Também é praticamente nulo. Não se testaram novas larguras ou penalidades buscando melhora nesses blocos. A variante instável anterior foi auditada no código e nas saídas do notebook, sem necessidade de reproduzir suas previsões explosivas.')
p('Esses modelos são NB2 com interações ambientais e bases gaussianas penalizadas; não são GWR/GWNB convencionais. Não foram produzidos mapas de significância local. A comparação histórica reutiliza blocos já examinados: os resultados são avaliação espacial de auditoria, não conjunto final intocado. Uma análise confirmatória exigirá protocolo congelado e avaliação independente.')
img('map_diagnostics.png')
# PAGE 8
page();h('7. Uso do solo, dados externos e limites')
p('Nenhum dos arquivos disponíveis permite medir proporções de parque, edificação, comércio ou estacionamento na célula. Sombra não é sinônimo de edifício: depende de geometria solar, horário e objetos que projetam sombra. Vegetação não é sinônimo de parque acessível. Não foram imputadas essas classes a partir dos percentuais ambientais.')
p('Foi identificada uma fonte municipal candidata: Uso do Solo Predominante Simples, 2014/2018/2021, PMSP/SMUL/SF, com dados fiscais de janeiro e cartografia de outubro de 2022, EPSG:31983. A unidade é a quadra fiscal, com cartografia de referência 1:1.000/1:5.000 e 16 tipologias; não é classificação de cada pixel ou de cada célula de 50 m. Cobertura fiscal incompleta e mudanças temporais limitam sua utilização. A licença geral GeoSampa informada pela Prefeitura é CC-BY-SA 4.0. Consulta em 23/09/2026. [1–3]')
p('A fonte é candidata para um controle anterior ou próximo ao período sugerido pelos campos 2022–2025, mas a janela dos crimes precisa ser confirmada. A tentativa de acesso WFS GetCapabilities retornou HTTP 502; o serviço também não foi recuperado pelo mecanismo de navegação. Nenhuma geometria externa foi incorporada. O registro técnico da tentativa está em external_access.txt. Não se confundiu zoneamento permitido com uso efetivamente observado.')
p('A rede local já permite a comparação viária, mas faltam data, licença, origem e regras de classificação. Não se atribuiu automaticamente a ela a licença do GeoSampa. Classes com nomes semelhantes podem provir de sistemas distintos. O conjunto de vias não mede capacidade, permissões de tráfego, volume de circulação, vagas ou permanência dos veículos.')
sub('Decisões científicas para a próxima etapa')
p('1. Definir o domínio: células cruzadas por vias, todas as células dos distritos ou locais com veículos expostos. Recomenda-se manter os 45.004 casos como análise de associação no domínio viário documentado, acompanhados das sensibilidades, sem apresentá-los como cobertura integral dos distritos.')
p('2. Confirmar fontes, período e construção dos desfechos; recuperar o script de agregação dos controles e o significado de VTR, infrastructure_index, high_income e moradores. Recuperar também limites dos 26 distritos, pontos criminais e a classificação ambiental/raster.')
p('3. Para avançar além de associação condicional, obter uso do solo e exposição com suporte espacial e temporal adequado. Uso fiscal por quadra pode ser controle contextual; não substitui estacionamentos, fluxo ou veículos-tempo. Não há justificativa empírica aqui para escolher 10 ou 25 m como corte principal definitivo.')
p('4. Não ampliar a complexidade local antes de resolver essas definições. A evidência disponível sustenta encerrar esta auditoria: a composição viária foi comparada; a lacuna de uso do solo foi demonstrada. Os originais foram preservados.')
# PAGE 9
page();h('8. Resumo em linguagem simples e reprodução')
p('<b>A sua grade não está cheia de células de parques sem rua:</b> as células sem linha viária já ficaram de fora. Isso não significa que as células restantes sejam ruas puras: cada quadrado pode conter árvores, prédios e outros usos ao redor do eixo viário.')
p('Cortar ainda mais a grade, exigindo classes motorizadas ou um trecho maior de via, mudou pouco a relação estimada entre vegetação, sombra e crimes. Levar em conta quanto de via existe e que tipo de via passa no quadrado mudou mais o resultado. Portanto, é mais produtivo documentar e controlar essas características do que excluir zeros ou procurar um corte que dê significância.')
p('Há uma pequena associação negativa para vegetação e uma positiva para sombra, dadas as variáveis usadas. A primeira continua incerta quando consideramos dependência em áreas maiores. Os modelos não demonstram que plantar árvores reduza crimes ou que produzir sombra aumente crimes. Também não permitem calcular o risco individual de um veículo.')
img('coefficients.png',475)
sub('Como conferir os resultados')
p('O pacote contém audit.py, models.py, spatial_cv.py e report.py, README com comandos, versões dos pacotes, hashes SHA-256 dos sete arquivos, tabelas CSV, figuras, logs e uma cópia derivada da grade com as medidas viárias. A derivada pode ser aberta no QGIS. Os scripts leem os originais e escrevem apenas em investigation/results.')
p('Não foram completados artificialmente dados ausentes; não foi filtrado nenhum grupo por apresentar ou não crimes. As comparações de seleções estão em selections.csv, as estimativas completas em coefficients.csv e os resultados por bloco em cv.csv. Os IC reportados são Wald exploratórios; não corrigem multiplicidade nem dependência que atravesse blocos.')
sub('Fontes externas consultadas (sem integração de camadas)')
p('[1] PMSP/SMUL/SF. Uso do Solo Predominante Simples 2014, 2018 e 2021. Metadado 73e0158b-2ec0-485c-b609-300f604afae7. https://metadados.geosampa.prefeitura.sp.gov.br/geonetwork/srv/api/records/73e0158b-2ec0-485c-b609-300f604afae7')
p('[2] PMSP. Licença para uso de dados do GeoSampa, 03/04/2025. https://prefeitura.sp.gov.br/web/licenciamento/w/licença-para-uso-de-dados-do-geosampa')
p('[3] PMSP/Geoinfo. Tutorial GeoSampa. https://geoinfo-smdu.github.io/tutorial-GeoSampa/')
p('[4] Statsmodels. NegativeBinomial: parametrização NB2. https://www.statsmodels.org/v0.12.2/generated/statsmodels.discrete.discrete_model.NegativeBinomial.html')
def footer(canvas,doc):
 canvas.setFont('Helvetica',8);canvas.setFillColor(colors.gray);canvas.drawString(45,25,'Auditoria computacional | São Paulo | 23/09/2026');canvas.drawRightString(A4[0]-45,25,str(doc.page))
doc=SimpleDocTemplate(str(out/'Nota_tecnica_vegetacao_crimes.pdf'),pagesize=A4,rightMargin=45,leftMargin=45,topMargin=38,bottomMargin=42,title='Auditoria da seleção espacial: vegetação, sombra e crimes',author='Pesquisa de Normando Codá Amazonas');doc.build(story,onFirstPage=footer,onLaterPages=footer)
(out/'Nota_tecnica_vegetacao_crimes.md').write_text('\n'.join(md),encoding='utf-8')
