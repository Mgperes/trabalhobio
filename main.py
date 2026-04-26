import math
import random

from mesa import Agent, Model
from mesa.datacollection import DataCollector
from mesa.space import SingleGrid

try:
    from mesa.visualization.ModularVisualization import ModularServer
    from mesa.visualization.modules import CanvasGrid, ChartModule, TextElement
except ImportError:
    ModularServer = None
    CanvasGrid = None
    ChartModule = None
    TextElement = None

# Configuracoes
LARGURA = 40
ALTURA = 40
NUM_AGENTES = 30
MAX_PASSOS = 250

TIPOS = {
    "rapido": {
        "passos_por_tick": 2,
        "cor": "#ff6b6b",
        "label": "Rapido",
    },
    "normal": {
        "passos_por_tick": 1,
        "cor": "#74b9ff",
        "label": "Normal",
    },
    "lento": {
        "passos_por_tick": 1,
        "cor": "#55efc4",
        "label": "Lento",
    },
}


class AgenteMultidao(Agent):
    def __init__(self, model, goal_x, goal_y, tipo):
        super().__init__(model)
        self.goal_x = goal_x
        self.goal_y = goal_y
        self.tipo = tipo
        self.chegou = False
        self.caminho = []

    def _esta_no_destino(self):
        return self.pos == (self.goal_x, self.goal_y)

    def _pode_mover_neste_tick(self):
        # Agentes lentos andam em metade dos ticks para criar diferenca de velocidade.
        if self.tipo == "lento" and self.model.passo_atual % 2 == 1:
            return False
        return True

    def _escolher_proximo_passo(self):
        vizinhos = self.model.grid.get_neighborhood(
            self.pos, moore=True, include_center=True, radius=1
        )

        candidatos = []
        for pos in vizinhos:
            if pos != self.pos and (not self.model.grid.is_cell_empty(pos)):
                continue

            # Penaliza celulas congestionadas para estimular desvio.
            ao_redor = self.model.grid.get_neighborhood(
                pos, moore=True, include_center=False, radius=1
            )
            ocupacao = sum(1 for p in ao_redor if not self.model.grid.is_cell_empty(p))
            dist_destino = math.hypot(self.goal_x - pos[0], self.goal_y - pos[1])
            score = dist_destino + 0.9 * ocupacao
            candidatos.append((score, random.random(), pos))

        if not candidatos:
            return self.pos

        candidatos.sort(key=lambda t: (t[0], t[1]))
        return candidatos[0][2]

    def step(self):
        if self.chegou:
            return

        if self._esta_no_destino():
            self.chegou = True
            return

        if not self._pode_mover_neste_tick():
            return

        passos = TIPOS[self.tipo]["passos_por_tick"]
        for _ in range(passos):
            if self.chegou:
                break

            prox = self._escolher_proximo_passo()
            if prox == self.pos:
                # Sem espaco para avancar: agente espera.
                break

            self.model.grid.move_agent(self, prox)
            self.caminho.append(self.pos)

            if self._esta_no_destino():
                self.chegou = True
                break


class BiocrowdsModel(Model):
    def __init__(
        self,
        largura=LARGURA,
        altura=ALTURA,
        num_agentes=NUM_AGENTES,
        max_passos=MAX_PASSOS,
    ):
        super().__init__()
        self.largura = largura
        self.altura = altura
        self.num_agentes = num_agentes
        self.max_passos = max_passos
        self.passo_atual = 0
        self.running = True
        self.centro_x = self.largura // 2
        self.centro_y = self.altura // 2

        self.grid = SingleGrid(self.largura, self.altura, torus=False)

        tipos_lista = ["rapido", "normal", "lento"]
        for i in range(self.num_agentes):
            tipo = tipos_lista[i % 3]
            x, y = self._posicao_livre_canto(i)
            gx = random.randint(max(1, self.centro_x - 2), min(self.largura - 2, self.centro_x + 2))
            gy = random.randint(max(1, self.centro_y - 2), min(self.altura - 2, self.centro_y + 2))

            agente = AgenteMultidao(
                model=self,
                goal_x=gx,
                goal_y=gy,
                tipo=tipo,
            )
            self.grid.place_agent(agente, (x, y))
            agente.caminho.append((x, y))

        self.datacollector = DataCollector(
            model_reporters={
                "Chegados": lambda m: m.chegados,
                "Ativos": lambda m: m.num_agentes - m.chegados,
            }
        )
        self.datacollector.collect(self)

    @property
    def chegou_todos(self):
        return self.chegados >= self.num_agentes

    @property
    def chegou_percentual(self):
        return (100.0 * self.chegados / self.num_agentes) if self.num_agentes else 0.0

    @property
    def chegados(self):
        return sum(1 for a in self.agents if a.chegou)

    def _posicao_livre_canto(self, indice):
        regioes = [
            (0, min(4, self.largura - 1), 0, min(4, self.altura - 1)),
            (max(0, self.largura - 5), self.largura - 1, 0, min(4, self.altura - 1)),
            (0, min(4, self.largura - 1), max(0, self.altura - 5), self.altura - 1),
            (max(0, self.largura - 5), self.largura - 1, max(0, self.altura - 5), self.altura - 1),
        ]

        x_min, x_max, y_min, y_max = regioes[indice % len(regioes)]

        for _ in range(500):
            x = random.randint(x_min, x_max)
            y = random.randint(y_min, y_max)
            if self.grid.is_cell_empty((x, y)):
                return x, y

        for x in range(self.largura):
            for y in range(self.altura):
                if self.grid.is_cell_empty((x, y)):
                    return x, y

        raise RuntimeError("Nao foi possivel encontrar celula livre para inicializar agente.")

    def step(self):
        if self.chegou_todos or self.passo_atual >= self.max_passos:
            self.running = False
            return

        self.agents.shuffle_do("step")
        self.passo_atual += 1
        self.datacollector.collect(self)

        if self.chegou_todos or self.passo_atual >= self.max_passos:
            self.running = False


def agente_portrayal(agent):
    if agent is None:
        return {}

    cor = "#b0b6be" if agent.chegou else TIPOS[agent.tipo]["cor"]

    return {
        "Shape": "circle",
        "Color": cor,
        "Filled": "true",
        "Layer": 1,
        "r": 0.7,
        "stroke_color": "#ffffff",
        "text": "",
    }


if TextElement is not None:

    class StatusElement(TextElement):
        def render(self, model):
            return (
                f"Passo: {model.passo_atual}/{model.max_passos} | "
                f"Chegados: {model.chegados}/{model.num_agentes} "
                f"({model.chegou_percentual:.1f}%)"
            )


def criar_servidor():
    if ModularServer is None:
        return None

    canvas = CanvasGrid(agente_portrayal, LARGURA, ALTURA, 780, 780)
    status = StatusElement()
    chart = ChartModule(
        [
            {"Label": "Chegados", "Color": "#55efc4"},
            {"Label": "Ativos", "Color": "#74b9ff"},
        ],
        data_collector_name="datacollector",
    )

    model_params = {
        "largura": LARGURA,
        "altura": ALTURA,
        "num_agentes": NUM_AGENTES,
        "max_passos": MAX_PASSOS,
    }

    server = ModularServer(
        BiocrowdsModel,
        [status, canvas, chart],
        "Biocrowds com Mesa",
        model_params,
    )
    server.port = 8521
    return server


if __name__ == "__main__":
    servidor = criar_servidor()

    if servidor is None:
        modelo = BiocrowdsModel()
        while modelo.running:
            modelo.step()

        print(
            f"Mesa 3.x detectado sem ModularServer. Simulacao concluida: "
            f"{modelo.chegados}/{modelo.num_agentes} agentes em {modelo.passo_atual} passos."
        )
    else:
        print("Abrindo visualizacao Mesa em http://127.0.0.1:8521")
        servidor.launch()
