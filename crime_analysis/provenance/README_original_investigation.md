# Auditoria da seleção espacial — São Paulo
Execução em 23/09/2026. Os arquivos originais são somente lidos. Resultados não causais.

## Executar
Coloque os sete arquivos fornecidos na pasta `upload/` (nomes originais). Extraia este pacote de forma que exista `investigation/` no diretório de trabalho.
Python 3.12; instale `requirements.txt`. Execute, nesta ordem:

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python investigation/audit.py upload
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python investigation/models.py
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python investigation/spatial_cv.py
OPENBLAS_NUM_THREADS=1 python investigation/verify.py
python investigation/report.py
```

A auditoria produz `results/audit_cells.gpkg`: cópia derivada da grade maior, com comprimento viário único, classes, máscaras de seleção e coordenadas. Pode ser aberta no QGIS. Não edita `fase9.qgz` nem os arquivos originais.
`input_sha256.json` permite conferir os dados de entrada. Não são incluídos os arquivos originais no pacote. Use os anexos desta conversa.

## Resultados
- `columns.csv`, `*_distributions.csv`, `variable_dictionary.csv`: tipos, ausentes, distribuições e limites das definições operacionais.
- `geometry_checks.json`, `control_inheritance.csv`, `qgis_sources.json`: verificações espaciais e proveniência.
- `selections.csv`: todas as populações, incluindo zeros e células sem vias.
- `models.csv`, `coefficients.csv`: AIC, dispersão, zeros, coeficientes e IC por agrupamento espacial (0=convencional; 500/1000/2000 m).
- `moran.csv`: resíduos de Pearson, pesos por distância normalizados por linha, 999 permutações, seed 42, teste bilateral centrado na esperança nula. As ilhas ficam com linha zero.
- `cv.csv`, `folds.csv`: cinco blocos KMeans (seed 42, n_init=20), distância entre centroides treino/teste >300m. Dados de teste nunca usados para padronizar nem ajustar. `target=motor25` restringe a avaliação aos mesmos alvos; o treino permanece na amostra completa.
- `spatial_cv.csv`: auditoria do piloto anterior (centros fixos por coordenadas da amostra) e versão com centros derivados só do treino. Largura 1500m, penalidade 100, 40 centros; nenhum hiperparâmetro selecionado nesta avaliação. Alpha fixado no ajuste global do treino. Não é GWR/GWNB.
- `geographic_coverage_1km.csv`: cobertura em quadrículas métricas; não distritos administrativos.
- `map_*.png`, `coefficients.png`: mapas e intervalos. Pontos quadrados representam centroides das células.

## Limitações e decisões
Classes viárias são as fornecidas, sem validar origem/ano. Motorizadas operacionalmente = LOCAL, COLETORA, ARTERIAL ou RODOVIA. VTR fica de fora da seleção estrita por definição desconhecida. Comprimentos de 10 e 25m são sensibilidades geométricas, não limiares físicos de exposição nem critérios escolhidos por significância. Nenhuma seleção utiliza crimes.
Comprimento é covariável, não offset: não representa veículos-tempo. Controles antigos mantidos sem log para reproduzir a especificação. Sem imputação artificial de controles inexistentes fora da rede.
AIC só compara modelos com o mesmo desfecho e as mesmas células. IC por blocos são exploratórios: não eliminam dependência entre blocos. CV reutiliza a geografia de avaliações históricas; não é um teste externo intocado.
O WFS externo do GeoSampa retornou HTTP 502 na tentativa de capacidades; nenhum polígono externo entrou nos modelos. A nota documenta dados candidatos, datas e licenciamento. `environmental_classification_final.gpkg` não estava acessível.

## Registro de correções
1. Saída Parquet dependia de pyarrow ausente: substituída por GPKG sem alterar os dados.
2. Inicialização padrão da NB2 com todos os controles viários convergiu espuriamente para alpha ~3,12e-9, AIC 74063,19, Hessiana inválida. Descartada. Inicialização explícita com coeficientes Poisson e alpha=5 produziu AIC 58786,04 e solução interior. O código entregue inclui a correção.
3. Avisos de indexação pandas resolvidos usando arrays e MultiIndex.
4. Pacotes ausentes foram instalados. Versões efetivas estão em requirements.txt.
5. O piloto histórico foi reotimizado com tolerância mais estrita; pequenas diferenças são reportadas, sem alegar igualdade exata.
