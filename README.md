# Biocrowds com Mesa

Trabalho acadêmico da disciplina Computação Científica : Simulação de fluxo de multidão baseada em agentes usando Mesa.
O projeto modela agentes com velocidades diferentes atravessando uma grade 2D até um destino próximo ao centro do mapa.

## Funcionalidades

- Simulação em grade com agentes rápidos, normais e lentos.
- Escolha de caminho com penalização de áreas congestionadas.
- Coleta de dados de agentes chegados e ativos.
- Visualização gráfica via Mesa, com fallback para execução em linha de comando quando a interface visual não estiver disponível.

## Requisitos

- Python 3.10 ou superior.
- Dependência principal: mesa.

## Instalação

Crie e ative um ambiente virtual, se desejar, e instale a dependência:

```bash
python -m pip install mesa
```

Se o comando python no Windows apontar para a Microsoft Store, use o launcher do Python instalado no sistema:

```bash
py -m pip install mesa
```

## Como executar

### Com interface gráfica

Execute o arquivo principal:

```bash
python main.py
```

Se a instalação da Mesa incluir os módulos de visualização, o servidor abrirá em http://127.0.0.1:8521.

### Sem interface gráfica

Se os módulos de visualização não estiverem disponíveis, o script executa a simulação em modo textual no terminal e mostra o resultado final.

## Estrutura do projeto

- main.py: modelo da simulação, agentes e servidor Mesa.
- assets/agentes/: imagens dos agentes usadas como referência visual do projeto.

## Parâmetros principais

Os valores padrão da simulação estão definidos em main.py:

- LARGURA: largura da grade.
- ALTURA: altura da grade.
- NUM_AGENTES: quantidade de agentes.
- MAX_PASSOS: limite máximo de passos da simulação.

## Observações

- O modelo distribui agentes nas bordas e define destinos próximos ao centro da grade.
- Ao longo da execução, o estado é coletado pelo DataCollector da Mesa.