"""
Servicio de Recetas - Economía Aya
Base de conocimiento de recetas colombianas populares con mapeo a productos del catálogo.
"""

from dataclasses import dataclass
from typing import Optional
import uuid


@dataclass
class IngredienteReceta:
    """Ingrediente de una receta con mapeo a producto del catálogo"""
    nombre: str
    cantidad: str
    busqueda_catalogo: str
    obligatorio: bool = True
    notas: str = ""
    producto_id: Optional[uuid.UUID] = None
    precio_estimado: float = 0.0


@dataclass
class Receta:
    """Receta completa con ingredientes mapeables al catálogo"""
    id: str
    nombre: str
    descripcion: str
    categoria: str
    tiempo_min: int
    porciones: int
    costo_estimado_cop: float
    imagen_url: Optional[str]
    ingredientes: list[IngredienteReceta]
    pasos: list[str]
    tags: list[str]


# ============================================================
# BASE DE CONOCIMIENTO: RECETAS COLOMBIANAS POPULARES
# ============================================================

RECETAS_BASE: list[Receta] = [
    Receta(
        id="huevos_pericos",
        nombre="Huevos Pericos con Arepa",
        descripcion="El desayuno clásico colombiano: huevos revueltos con cebolla y tomate, acompañados de arepa con mantequilla",
        categoria="desayuno",
        tiempo_min=15,
        porciones=2,
        costo_estimado_cop=22000,
        imagen_url=None,
        ingredientes=[
            IngredienteReceta("Huevos AAA", "3 unidades", "huevos AAA docena", notas="frescos"),
            IngredienteReceta("Cebolla cabezona", "1/2 unidad", "cebolla cabezona", notas="picada en cubitos pequeños"),
            IngredienteReceta("Tomate riñón", "1 grande", "tomate riñón", notas="picado en cubitos, sin semillas"),
            IngredienteReceta("Arepa de maíz", "2 unidades", "arepa maiz", notas="para acompañar"),
            IngredienteReceta("Mantequilla", "1 cucharada", "mantequilla", obligatorio=False, notas="para la arepa"),
            IngredienteReceta("Sal", "al gusto", "sal", obligatorio=False),
            IngredienteReceta("Aceite", "1 cucharada", "aceite vegetal", obligatorio=False, notas="para cocinar"),
        ],
        pasos=[
            "Pica la cebolla y el tomate en cubitos muy pequeños",
            "Calienta el aceite en una sartén a fuego medio",
            "Sofríe la cebolla 2-3 min hasta que esté transparente",
            "Añade el tomate y cocina 2 min más hasta que suelte jugo",
            "Bate los huevos con sal y viértelos sobre el sofrito",
            "Revuelve suavemente con espátula hasta que estén cremosos (no secos)",
            "Tuesta las arepas y úntalas con mantequilla",
            "Sirve los huevos pericos calientes con las arepas al lado",
        ],
        tags=["tradicional", "facil", "rapido", "economico", "proteina"],
    ),

    Receta(
        id="calentado_paisa",
        nombre="Calentado Paisa",
        descripcion="El almuerzo de los domingos: arroz, frijoles, carne, plátano maduro, huevo frito y arepa. ¡Completo!",
        categoria="almuerzo",
        tiempo_min=25,
        porciones=2,
        costo_estimado_cop=35000,
        imagen_url=None,
        ingredientes=[
            IngredienteReceta("Arroz blanco", "2 tazas cocido", "arroz blanco", notas="idealmente del día anterior"),
            IngredienteReceta("Frijoles rojos", "1 taza cocidos", "frijoles rojos", notas="cargados, con su caldo"),
            IngredienteReceta("Carne molida", "200g", "carne molida", notas="sofreída con cebolla, ajo, comino"),
            IngredienteReceta("Plátano maduro", "2 unidades", "platano maduro", notas="fritos en rodajas diagonales"),
            IngredienteReceta("Huevos AAA", "2 unidades", "huevos AAA", notas="fritos, yema suave"),
            IngredienteReceta("Arepa de maíz", "2 unidades", "arepa maiz"),
            IngredienteReceta("Aguacate", "1/2 unidad", "aguacate hass", obligatorio=False, notas="en láminas"),
            IngredienteReceta("Hogao", "3 cucharadas", "hogao", obligatorio=False, notas="tomate, cebolla, ajo"),
        ],
        pasos=[
            "Calienta el arroz y los frijoles por separado",
            "Fríe el plátano maduro en aceite caliente hasta dorar",
            "Fríe los huevos con yema suave",
            "Calienta la carne molida si es del día anterior",
            "Tuesta las arepas",
            "Sirve en plato hondo: base de arroz, frijoles al lado, carne encima",
            "Acompaña con plátano, huevo frito, arepa y aguacate",
        ],
        tags=["tradicional", "completo", "contundente", "fin_de_semana"],
    ),

    Receta(
        id="changua",
        nombre="Changua Bogotana",
        descripcion="Sopa de leche con huevo, cebolla larga y pan. El desayuno bogotano por excelencia, calentita y reconfortante",
        categoria="desayuno",
        tiempo_min=15,
        porciones=2,
        costo_estimado_cop=12000,
        imagen_url=None,
        ingredientes=[
            IngredienteReceta("Leche entera", "4 tazas", "leche entera", notas="1 litro aprox"),
            IngredienteReceta("Huevos AAA", "2 unidades", "huevos AAA"),
            IngredienteReceta("Cebolla larga", "2 tallos", "cebolla larga", notas="picada finita, parte verde y blanca"),
            IngredienteReceta("Pan calado", "2 rebanadas", "pan calado", notas="o pan francés, tostado"),
            IngredienteReceta("Queso campesino", "50g", "queso campesino", notas="desmenuzado"),
            IngredienteReceta("Sal", "al gusto", "sal", obligatorio=False),
            IngredienteReceta("Cilantro", "1 ramita", "cilantro", obligatorio=False, notas="picado para decorar"),
        ],
        pasos=[
            "Calienta la leche en olla grande a fuego medio (no dejes que hierva fuerte)",
            "Cuando esté caliente, baja el fuego y rompe los huevos con cuidado",
            "Cocina 3-4 min hasta que la clara cuaje pero la yema esté suave",
            "Añade la cebolla larga y sal, retira del fuego",
            "Tuesta el pan y ponlo en el fondo del plato hondo",
            "Sirve la changua con los huevos, espolvorea queso y cilantro",
        ],
        tags=["tradicional", "bogotano", "reconfortante", "economico", "ligero"],
    ),

    Receta(
        id="ajiaco",
        nombre="Ajiaco Santafereño",
        descripcion="La sopa insignia de Bogotá: pollo, tres papas, mazorca, guasca, alcaparras y crema. ¡Un plato completo en un tazón!",
        categoria="almuerzo",
        tiempo_min=90,
        porciones=6,
        costo_estimado_cop=55000,
        imagen_url=None,
        ingredientes=[
            IngredienteReceta("Pollo entero", "1 kg (muslos/presas)", "pollo", notas="con hueso para más sabor"),
            IngredienteReceta("Papa pastusa", "500g", "papa pastusa", notas="se deshace y espesa el caldo"),
            IngredienteReceta("Papa criolla", "500g", "papa criolla", notas="pequeñas, amarillas, se mantienen enteras"),
            IngredienteReceta("Papa sabanera", "300g", "papa sabanera", notas="blancas, almidonadas"),
            IngredienteReceta("Mazorca", "3 unidades", "mazorca", notas="en trozos de 3-4 cm"),
            IngredienteReceta("Guasca fresca", "1 manojo", "guasca", notas="¡esencial! da el sabor único"),
            IngredienteReceta("Cebolla cabezona", "1 grande", "cebolla cabezona", notas="picada"),
            IngredienteReceta("Ajo", "3 dientes", "ajo", notas="machacado"),
            IngredienteReceta("Alcaparras", "2 cucharadas", "alcaparras", obligatorio=False),
            IngredienteReceta("Crema de leche", "200ml", "crema de leche", obligatorio=False),
            IngredienteReceta("Arroz blanco", "para acompañar", "arroz blanco", obligatorio=False),
            IngredienteReceta("Aguacate", "1 unidad", "aguacate hass", obligatorio=False),
        ],
        pasos=[
            "En olla grande, hierve agua con pollo, cebolla, ajo y sal 45 min",
            "Retira pollo, desmecha y devuelve carne al caldo",
            "Añade papas pastusa y sabanera, cocina 15 min",
            "Agrega papa criolla y mazorca, cocina 10 min más",
            "Incorpora guasca fresca, cocina 5 min y apaga",
            "Sirve con alcaparras, crema, arroz y aguacate al lado",
        ],
        tags=["tradicional", "bogotano", "especial", "completo", "para_compartir"],
    ),

    Receta(
        id="sancocho",
        nombre="Sancocho Trifásico",
        descripcion="El rey de las sopas colombianas: tres carnes, yuca, plátano, papa, mazorca y cilantro. Para reuniones familiares",
        categoria="almuerzo",
        tiempo_min=120,
        porciones=8,
        costo_estimado_cop=85000,
        imagen_url=None,
        ingredientes=[
            IngredienteReceta("Costilla de res", "1 kg", "costilla res"),
            IngredienteReceta("Pollo", "1 kg (presas)", "pollo"),
            IngredienteReceta("Cerdo (tocineta/costilla)", "500g", "cerdo"),
            IngredienteReceta("Yuca", "1 kg", "yuca", notas="pelada en trozos grandes"),
            IngredienteReceta("Plátano verde", "3 unidades", "platano verde", notas="en trozos con cáscara"),
            IngredienteReceta("Papa pastusa", "500g", "papa pastusa"),
            IngredienteReceta("Papa criolla", "500g", "papa criolla"),
            IngredienteReceta("Mazorca", "4 unidades", "mazorca", notas="en trozos"),
            IngredienteReceta("Cilantro", "1 manojo grande", "cilantro", notas="picado, al final"),
            IngredienteReceta("Cebolla larga", "3 tallos", "cebolla larga"),
            IngredienteReceta("Ajo", "4 dientes", "ajo"),
            IngredienteReceta("Comino", "1 cucharadita", "comino", obligatorio=False),
            IngredienteReceta("Arroz blanco", "para acompañar", "arroz blanco", obligatorio=False),
            IngredienteReceta("Aguacate", "2 unidades", "aguacate hass", obligatorio=False),
            IngredienteReceta("Limón", "2 unidades", "limon", obligatorio=False),
        ],
        pasos=[
            "Hierve carnes duras (res, cerdo) 45 min con cebolla, ajo, sal",
            "Añade pollo y cocina 20 min más",
            "Incorpora yuca, plátano verde, mazorca - 15 min",
            "Agrega papas - 15 min hasta que todo esté tierno",
            "Apaga fuego, añade cilantro y comino",
            "Sirve carnes y vegetales en tazón grande con caldo",
            "Acompaña con arroz, aguacate y limón",
        ],
        tags=["tradicional", "familiar", "fiesta", "completo", "trifasico"],
    ),

    Receta(
        id="patacones_hogao",
        nombre="Patacones con Hogao",
        descripcion="Plátano verde aplastado y frito dos veces, crujiente por fuera y suave por dentro, con hogao casero encima",
        categoria="acompanamiento",
        tiempo_min=20,
        porciones=4,
        costo_estimado_cop=15000,
        imagen_url=None,
        ingredientes=[
            IngredienteReceta("Plátano verde", "4 unidades", "platano verde", notas="bien verdes, duros"),
            IngredienteReceta("Aceite vegetal", "para freír", "aceite vegetal", notas="abundante, 350°F"),
            IngredienteReceta("Sal", "al gusto", "sal"),
            IngredienteReceta("Tomate riñón", "2 grandes", "tomate riñón", notas="para hogao, picado en cubitos"),
            IngredienteReceta("Cebolla cabezona", "1 grande", "cebolla cabezona", notas="para hogao, picada fina"),
            IngredienteReceta("Ajo", "2 dientes", "ajo", notas="para hogao, machacado"),
            IngredienteReceta("Comino", "1/2 cucharadita", "comino", obligatorio=False, notas="para hogao"),
            IngredienteReceta("Color", "1 pizca", "color", obligatorio=False, notas="para hogao"),
        ],
        pasos=[
            "Pela plátanos y corta en trozos de 4-5 cm",
            "Fríe primera vez 2-3 min a 320°F (blanqueo)",
            "Escurre, aplasta con tostonera o fondo de vaso",
            "Fríe segunda vez 2-3 min a 350°F hasta dorar y crujir",
            "Escurre en papel absorbente, sal al gusto",
            "Para hogao: sofríe cebolla, ajo, tomate, comino, color 10 min",
            "Sirve patacones con hogao por encima",
        ],
        tags=["tradicional", "crujiente", "aperitivo", "compartir", "vegano"],
    ),

    Receta(
        id="arepas_queso",
        nombre="Arepas de Queso Costeño",
        descripcion="Arepas de maíz rellenas de queso costeño derretido, doradas en mantequilla. Desayuno o merienda perfecta",
        categoria="desayuno",
        tiempo_min=15,
        porciones=4,
        costo_estimado_cop=18000,
        imagen_url=None,
        ingredientes=[
            IngredienteReceta("Arepa de maíz", "4 unidades", "arepa maiz", notas="pre-cocidas o crudas"),
            IngredienteReceta("Queso costeño", "200g", "queso costeño", notas="rallado o en láminas"),
            IngredienteReceta("Mantequilla", "2 cucharadas", "mantequilla", notas="para dorar"),
            IngredienteReceta("Queso mozzarella", "100g", "queso mozzarella", obligatorio=False, notas="mezcla extra derretida"),
        ],
        pasos=[
            "Si arepas crudas: cocina 5 min por lado en budare/sartén",
            "Corta arepa a lo largo (tipo sándwich) sin separar del todo",
            "Rellena generosamente con queso costeño (+ mozzarella opcional)",
            "Unta mantequilla por fuera",
            "Dora en sartén 2-3 min por lado hasta que queso derrita",
            "Sirve caliente, el queso debe estirarse",
        ],
        tags=["tradicional", "costeño", "derretido", "rapido", "merienda"],
    ),

    Receta(
        id="lentejas",
        nombre="Lentejas con Chorizo",
        descripcion="Lentejas guisadas con chorizo, zanahoria, papa y cilantro. Nutritivas, económicas y reconfortantes",
        categoria="almuerzo",
        tiempo_min=45,
        porciones=4,
        costo_estimado_cop=20000,
        imagen_url=None,
        ingredientes=[
            IngredienteReceta("Lentejas", "500g", "lentejas", notas="remojadas 2h o toda la noche"),
            IngredienteReceta("Chorizo", "200g", "chorizo", notas="en rodajas"),
            IngredienteReceta("Zanahoria", "2 medianas", "zanahoria", notas="en cubitos"),
            IngredienteReceta("Papa pastusa", "2 medianas", "papa pastusa", notas="en cubitos"),
            IngredienteReceta("Cebolla cabezona", "1 grande", "cebolla cabezona"),
            IngredienteReceta("Ajo", "3 dientes", "ajo"),
            IngredienteReceta("Tomate riñón", "1 grande", "tomate riñón"),
            IngredienteReceta("Comino", "1 cucharadita", "comino"),
            IngredienteReceta("Laurel", "2 hojas", "laurel", obligatorio=False),
            IngredienteReceta("Cilantro", "1 manojo", "cilantro", notas="picado, al final"),
            IngredienteReceta("Arroz blanco", "para acompañar", "arroz blanco", obligatorio=False),
        ],
        pasos=[
            "Escurre lentejas remojadas",
            "Sofríe chorizo hasta soltar grasa, retira y reserva",
            "En misma grasa sofríe cebolla, ajo, tomate, comino",
            "Añade lentejas, zanahoria, papa, laurel y agua (3x vol lentejas)",
            "Cocina 25-30 min hasta que lentejas estén tiernas",
            "Incorpora chorizo reservado, cilantro, ajusta sal",
            "Sirve con arroz blanco",
        ],
        tags=["tradicional", "economico", "nutritivo", "legumbres", "reconfortante"],
    ),

    Receta(
        id="arroz_pollo",
        nombre="Arroz con Pollo",
        descripcion="El clásico de las fiestas: arroz amarillo con pollo, arvejas, zanahoria y especias. Colorido y sabroso",
        categoria="almuerzo",
        tiempo_min=50,
        porciones=6,
        costo_estimado_cop=40000,
        imagen_url=None,
        ingredientes=[
            IngredienteReceta("Pollo", "1 kg (muslos/contramuslos)", "pollo", notas="con piel y hueso"),
            IngredienteReceta("Arroz blanco", "3 tazas", "arroz blanco"),
            IngredienteReceta("Arvejas", "1 taza", "arvejas", notas="congeladas o frescas"),
            IngredienteReceta("Zanahoria", "2 medianas", "zanahoria", notas="en cubitos pequeños"),
            IngredienteReceta("Cebolla cabezona", "1 grande", "cebolla cabezona"),
            IngredienteReceta("Ajo", "4 dientes", "ajo"),
            IngredienteReceta("Tomate riñón", "1 grande", "tomate riñón"),
            IngredienteReceta("Pimentón", "1 unidad", "pimenton", notas="rojo, en tiras"),
            IngredienteReceta("Color/Azafrán", "1 cucharada", "color", notas="para el color amarillo"),
            IngredienteReceta("Comino", "1 cucharadita", "comino"),
            IngredienteReceta("Caldo de pollo", "6 tazas", "caldo pollo", notas="o agua + cubo caldo"),
            IngredienteReceta("Cilantro", "1 manojo", "cilantro", obligatorio=False),
        ],
        pasos=[
            "Sella pollo en aceite caliente hasta dorar, reserva",
            "En misma olla sofríe cebolla, ajo, tomate, pimentón",
            "Añade arroz, revuelve 1 min para nacarar",
            "Agrega color, comino, caldo hirviendo y pollo",
            "Hierve, tapa y cocina 15 min fuego bajo",
            "Añade arvejas y zanahoria encima, tapa 5 min más",
            "Apaga, deja reposar tapado 10 min, esponja con tenedor",
            "Espolvorea cilantro y sirve",
        ],
        tags=["tradicional", "fiesta", "familiar", "colorido", "completo"],
    ),

    Receta(
        id="pasta_bolognesa",
        nombre="Pasta Bolognesa Casera",
        descripcion="Espagueti con salsa de carne lenta, tomate, verduras y hierbas. Comfort food universal con toque colombiano",
        categoria="cena",
        tiempo_min=40,
        porciones=4,
        costo_estimado_cop=28000,
        imagen_url=None,
        ingredientes=[
            IngredienteReceta("Espagueti", "400g", "espagueti", notas="o pasta corta tipo pluma"),
            IngredienteReceta("Carne molida", "400g", "carne molida"),
            IngredienteReceta("Tomate triturado", "800g", "tomate triturado", notas="o 4 tomates riñón licuados"),
            IngredienteReceta("Cebolla cabezona", "1 grande", "cebolla cabezona"),
            IngredienteReceta("Zanahoria", "1 mediana", "zanahoria", notas="rallada fina"),
            IngredienteReceta("Apio", "1 tallo", "apio", notas="picado fino, opcional"),
            IngredienteReceta("Ajo", "3 dientes", "ajo"),
            IngredienteReceta("Vino tinto", "1/2 taza", "vino tinto", obligatorio=False),
            IngredienteReceta("Orégano", "1 cucharadita", "orégano"),
            IngredienteReceta("Albahaca", "1 cucharadita", "albahaca", obligatorio=False),
            IngredienteReceta("Queso parmesano", "para servir", "queso parmesano", obligatorio=False),
        ],
        pasos=[
            "Sofríe cebolla, zanahoria, apio, ajo en aceite 8 min",
            "Añade carne, rompe con cuchara, dora bien 10 min",
            "Desglasa con vino (si usas), evapora alcohol 2 min",
            "Incorpora tomate, orégano, sal, pimienta, hierve",
            "Baja fuego, tapa y cocina 20 min removiendo ocasional",
            "Cuece pasta al dente en agua con sal",
            "Mezcla pasta con salsa, sirve con albahaca y parmesano",
        ],
        tags=["internacional", "familiar", "ninos", "congelable", "cena"],
    ),

    Receta(
        id="tostones_guacamole",
        nombre="Tostones con Guacamole",
        descripcion="Plátano verde frito y aplastado, crujiente, con guacamole fresco de aguacate, limón y cilantro",
        categoria="snack",
        tiempo_min=20,
        porciones=4,
        costo_estimado_cop=22000,
        imagen_url=None,
        ingredientes=[
            IngredienteReceta("Plátano verde", "4 unidades", "platano verde"),
            IngredienteReceta("Aceite vegetal", "para freír", "aceite vegetal"),
            IngredienteReceta("Sal", "al gusto", "sal"),
            IngredienteReceta("Aguacate hass", "2 grandes", "aguacate hass", notas="maduros, suaves"),
            IngredienteReceta("Limón", "1 unidad", "limon", notas="jugo"),
            IngredienteReceta("Cebolla cabezona", "1/4 unidad", "cebolla cabezona", notas="picada minúscula"),
            IngredienteReceta("Cilantro", "1 ramita", "cilantro", notas="picado"),
            IngredienteReceta("Tomate riñón", "1 pequeño", "tomate riñón", obligatorio=False, notas="en cubitos, sin semillas"),
            IngredienteReceta("Chile", "al gusto", "chile", obligatorio=False, notas="picante opcional"),
        ],
        pasos=[
            "Pela y corta plátanos en trozos de 3-4 cm",
            "Fríe primera vez 2 min a 320°F, escurre",
            "Aplasta con tostonera hasta 1 cm grosor",
            "Fríe segunda vez 2-3 min a 350°F hasta dorar",
            "Sal al gusto inmediato",
            "Guacamole: aplasta aguacate, mezcla limón, cebolla, cilantro, tomate, sal",
            "Sirve tostones calientes con guacamole al lado",
        ],
        tags=["snack", "vegano", "fresco", "compartir", "aperitivo"],
    ),

    Receta(
        id="hamburguesa_casera",
        nombre="Hamburguesa Casera Colombiana",
        descripcion="Hamburguesa jugosa con carne 100% res, queso derretido, lechuga, tomate, cebolla y salsas. ¡Mejor que la de la esquina!",
        categoria="almuerzo",
        tiempo_min=25,
        porciones=4,
        costo_estimado_cop=38000,
        imagen_url=None,
        ingredientes=[
            IngredienteReceta("Hamburguesa de Res 100%", "4 unidades (500g)", "hamburguesa res", notas="carne molida pura"),
            IngredienteReceta("Pan de Hamburguesa", "4 unidades", "pan hamburguesa", notas="con semillas de sésamo"),
            IngredienteReceta("Queso Americano", "4 láminas", "queso americano", notas="se derrite perfecto"),
            IngredienteReceta("Lechuga Crespa", "4 hojas", "lechuga crespa", notas="lavada y seca"),
            IngredienteReceta("Tomate riñón", "1 grande", "tomate riñón", notas="en rodajas, sin semillas"),
            IngredienteReceta("Cebolla cabezona", "1/2 unidad", "cebolla cabezona", notas="en aros finos"),
            IngredienteReceta("Salsa Kétchup", "al gusto", "ketchup"),
            IngredienteReceta("Mayonesa", "al gusto", "mayonesa", obligatorio=False),
            IngredienteReceta("Mostaza", "al gusto", "mostaza", obligatorio=False),
            IngredienteReceta("Pepinillos", "al gusto", "pepinillos", obligatorio=False, notas="en rodajas"),
        ],
        pasos=[
            "Calienta plancha/sartén a fuego medio-alto con gota de aceite",
            "Sazona las hamburguesas con sal y pimienta",
            "Cocina 3-4 min por lado (no aplastes, pierden jugo)",
            "Último minuto: pon queso encima y tapa para que derrita",
            "Tuesta panes en la plancha 1 min (lado cortado hacia abajo)",
            "Arma: pan base + mayonesa/mostaza + lechuga + carne con queso + tomate + cebolla + kétchup + pan tapa",
            "Sirve inmediato con papas fritas o ensalada",
        ],
        tags=["casera", "jugosa", "familiar", "rapido", "favorita"],
    ),

    Receta(
        id="sopa_verdur",
        nombre="Sopa de Verduras Criolla",
        descripcion="Sopa ligera y nutritiva: zanahoria, papa, apio, cebolla, cilantro en caldo casero. Ideal para cenas ligeras o cuando estás malo",
        categoria="cena",
        tiempo_min=35,
        porciones=4,
        costo_estimado_cop=15000,
        imagen_url=None,
        ingredientes=[
            IngredienteReceta("Zanahoria", "2 medianas", "zanahoria", notas="en rodajas o cubitos"),
            IngredienteReceta("Papa pastusa", "2 medianas", "papa pastusa", notas="en cubitos"),
            IngredienteReceta("Apio", "2 tallos", "apio", notas="en rodajas finas"),
            IngredienteReceta("Cebolla cabezona", "1 mediana", "cebolla cabezona"),
            IngredienteReceta("Ajo", "2 dientes", "ajo"),
            IngredienteReceta("Tomate riñón", "1 grande", "tomate riñón", notas="picado"),
            IngredienteReceta("Caldo de verduras", "2 litros", "caldo verduras", notas="o agua + cubo caldo"),
            IngredienteReceta("Cilantro", "1 manojo", "cilantro", notas="picado, al final"),
            IngredienteReceta("Comino", "1/2 cucharadita", "comino", obligatorio=False),
            IngredienteReceta("Limón", "1 unidad", "limon", obligatorio=False, notas="gotas al servir"),
        ],
        pasos=[
            "Sofríe cebolla, ajo, tomate, comino en aceite 5 min",
            "Añade caldo hirviendo, zanahoria, papa, apio",
            "Hierve, tapa y cocina 20 min hasta verduras tiernas",
            "Apaga, añade cilantro, deja reposar 5 min tapado",
            "Sirve con gotas de limón",
        ],
        tags=["ligero", "saludable", "vegano", "economico", "reconfortante", "cena_ligera"],
    ),

    Receta(
        id="bandeja_paisa",
        nombre="Bandeja Paisa",
        descripcion="El plato bandera de Antioquia: frijoles, arroz, carne molida, chicharrón, huevo frito, plátano, arepa, aguacate y morcilla. ¡Un festín!",
        categoria="almuerzo",
        tiempo_min=90,
        porciones=2,
        costo_estimado_cop=55000,
        imagen_url=None,
        ingredientes=[
            IngredienteReceta("Frijoles rojos", "500g", "frijoles rojos", notas="cargados, con su caldo espeso"),
            IngredienteReceta("Arroz blanco", "2 tazas", "arroz blanco"),
            IngredienteReceta("Carne molida", "300g", "carne molida", notas="sofreída con hogao"),
            IngredienteReceta("Chicharrón", "200g", "chicharron", notas="crujiente"),
            IngredienteReceta("Chorizo", "2 unidades", "chorizo", notas="santarrosano"),
            IngredienteReceta("Morcilla", "1 unidad", "morcilla", obligatorio=False),
            IngredienteReceta("Huevos AAA", "2 unidades", "huevos AAA", notas="fritos, yema suave"),
            IngredienteReceta("Plátano maduro", "2 unidades", "platano maduro", notas="fritos en rodajas"),
            IngredienteReceta("Arepa de maíz", "2 unidades", "arepa maiz"),
            IngredienteReceta("Aguacate hass", "1 unidad", "aguacate hass", notas="en láminas"),
            IngredienteReceta("Hogao", "4 cucharadas", "hogao", notas="tomate, cebolla, ajo, comino"),
        ],
        pasos=[
            "Cocina frijoles 2h hasta que estén suaves y el caldo espeso",
            "Prepara arroz blanco suelto",
            "Sofríe carne molida con hogao",
            "Fríe chicharrón y chorizo hasta dorar",
            "Fríe plátano maduro y huevos",
            "Tuesta arepas y calienta morcilla si usas",
            "Sirve en bandeja grande: frijoles, arroz, carnes, huevo, plátano, arepa, aguacate",
            "Acompaña con hogao por encima",
        ],
        tags=["tradicional", "paisa", "contundente", "fiesta", "completo", "iconico"],
    ),

    Receta(
        id="fritanga",
        nombre="Fritanga Colombiana",
        descripcion="Variedad de fritos para compartir: chicharrón, morcilla, longaniza, papa salada, arepa, yuca, plátano. Ideal para el domingo",
        categoria="almuerzo",
        tiempo_min=45,
        porciones=4,
        costo_estimado_cop=45000,
        imagen_url=None,
        ingredientes=[
            IngredienteReceta("Chicharrón", "500g", "chicharron", notas="en trozos medianos"),
            IngredienteReceta("Morcilla", "2 unidades", "morcilla"),
            IngredienteReceta("Longaniza/chorizo", "4 unidades", "chorizo"),
            IngredienteReceta("Papa pastusa", "1kg", "papa pastusa", notas="en gajos, con cáscara"),
            IngredienteReceta("Yuca", "1kg", "yuca", notas="en trozos grandes"),
            IngredienteReceta("Plátano verde", "4 unidades", "platano verde", notas="en trozos diagonales"),
            IngredienteReceta("Arepa de maíz", "4 unidades", "arepa maiz"),
            IngredienteReceta("Aceite vegetal", "abundante", "aceite vegetal", notas="para freír todo"),
            IngredienteReceta("Sal gruesa", "al gusto", "sal"),
            IngredienteReceta("Limón", "2 unidades", "limon", obligatorio=False, notas="para exprimir"),
            IngredienteReceta("Ají casero", "al gusto", "aji", obligatorio=False),
        ],
        pasos=[
            "Hierve papa y yuca 10 min, escurre",
            "Calienta aceite abundante a 180°C",
            "Fríe chicharrón hasta crujiente, retira",
            "Fríe longaniza y morcilla, retira",
            "Fríe papa, yuca y plátano hasta dorar",
            "Tuesta arepas en budare/sartén",
            "Sirve todo en bandeja grande con sal gruesa, limón y ají",
        ],
        tags=["tradicional", "compartir", "domingo", "fritos", "familiar", "contundente"],
    ),

    Receta(
        id="empanadas",
        nombre="Empanadas Criollas de Carne",
        descripcion="Empanadas de maíz rellenas de carne, papa, arvejas y hogao. Crujientes por fuera, jugosas por dentro",
        categoria="snack",
        tiempo_min=60,
        porciones=12,
        costo_estimado_cop=25000,
        imagen_url=None,
        ingredientes=[
            IngredienteReceta("Harina de maíz precocida", "500g", "harina maiz", notas="tipo PAN o similar"),
            IngredienteReceta("Carne molida", "300g", "carne molida"),
            IngredienteReceta("Papa pastusa", "2 medianas", "papa pastusa", notas="cocidas y machacadas"),
            IngredienteReceta("Arvejas", "1 taza", "arvejas", notas="cocidas"),
            IngredienteReceta("Cebolla cabezona", "1 grande", "cebolla cabezona", notas="para hogao"),
            IngredienteReceta("Tomate riñón", "1 grande", "tomate riñón", notas="para hogao"),
            IngredienteReceta("Ajo", "3 dientes", "ajo", notas="para hogao"),
            IngredienteReceta("Comino", "1 cucharadita", "comino"),
            IngredienteReceta("Color", "1 cucharadita", "color", obligatorio=False),
            IngredienteReceta("Aceite vegetal", "para freír", "aceite vegetal"),
            IngredienteReceta("Sal y pimienta", "al gusto", "sal"),
        ],
        pasos=[
            "Haz hogao: sofríe cebolla, ajo, tomate, comino, color",
            "Añade carne, dora bien, agrega papa y arvejas, mezcla",
            "Prepara masa: harina + agua tibia + sal, amasa hasta suave",
            "Haz bolitas, aplana, pon relleno, cierra y sella bordes",
            "Fríe en aceite caliente (180°C) 3-4 min hasta dorar",
            "Escurre en papel absorbente, sirve con ají",
        ],
        tags=["tradicional", "crujiente", "merienda", "compartir", "congelable", "antojito"],
    ),

    Receta(
        id="tamales",
        nombre="Tamales Tolimenses",
        descripcion="Tamales de maíz con carne, arvejas, zanahoria, papa, huevo y especias, envueltos en hoja de plátano. Tradición navideña",
        categoria="almuerzo",
        tiempo_min=180,
        porciones=10,
        costo_estimado_cop=80000,
        imagen_url=None,
        ingredientes=[
            IngredienteReceta("Harina de maíz", "2kg", "harina maiz", notas="para tamales"),
            IngredienteReceta("Costilla de cerdo", "1.5kg", "cerdo", notas="en trozos"),
            IngredienteReceta("Pechuga de pollo", "500g", "pollo", notas="en trozos"),
            IngredienteReceta("Arvejas", "2 tazas", "arvejas"),
            IngredienteReceta("Zanahoria", "3 medianas", "zanahoria", notas="en cubitos"),
            IngredienteReceta("Papa pastusa", "4 medianas", "papa pastusa", notas="en cubitos"),
            IngredienteReceta("Huevos AAA", "6 unidades", "huevos AAA", notas="cocidos, en cuartos"),
            IngredienteReceta("Cebolla cabezona", "2 grandes", "cebolla cabezona"),
            IngredienteReceta("Ajo", "6 dientes", "ajo"),
            IngredienteReceta("Comino", "2 cucharadas", "comino"),
            IngredienteReceta("Color/Achiote", "2 cucharadas", "color"),
            IngredienteReceta("Hojas de plátano", "20 unidades", "hojas platano", notas="pasadas por fuego"),
            IngredienteReceta("Manteca de cerdo", "300g", "manteca cerdo", notas="para la masa"),
            IngredienteReceta("Caldo de carne", "2 litros", "caldo pollo", notas="para la masa"),
        ],
        pasos=[
            "Cocina carnes con cebolla, ajo, comino, color 45 min",
            "Desmecha carnes, reserva caldo",
            "Mezcla harina con caldo tibio y manteca hasta masa suave",
            "En hoja de plátano: masa, carne, arvejas, zanahoria, papa, huevo",
            "Envuelve bien, ata con pabilo o tira de hoja",
            "Hierve en olla grande 2-3 horas",
            "Sirve caliente con chocolate caliente",
        ],
        tags=["tradicional", "tolima", "navidad", "familiar", "especial", "laborioso"],
    ),

    Receta(
        id="lechona",
        nombre="Lechona Tolimense",
        descripcion="Cerdo entero relleno de arroz, arvejas y especias, horneado hasta que la piel queda crujiente (cuerito). ¡La reina de las fiestas!",
        categoria="almuerzo",
        tiempo_min=480,
        porciones=30,
        costo_estimado_cop=400000,
        imagen_url=None,
        ingredientes=[
            IngredienteReceta("Cerdo entero (lechón)", "1 unidad (25-30kg)", "lechon", notas="limpio, sin vísceras"),
            IngredienteReceta("Arroz blanco", "5kg", "arroz blanco"),
            IngredienteReceta("Arvejas verdes", "3kg", "arvejas"),
            IngredienteReceta("Cebolla cabezona", "3kg", "cebolla cabezona", notas="picada fina"),
            IngredienteReceta("Ajo", "2 cabezas", "ajo", notas="machacado"),
            IngredienteReceta("Comino", "100g", "comino"),
            IngredienteReceta("Color/Achiote", "50g", "color"),
            IngredienteReceta("Sal", "200g", "sal"),
            IngredienteReceta("Pimienta", "50g", "pimienta", obligatorio=False),
            IngredienteReceta("Manteca de cerdo", "2kg", "manteca cerdo", notas="para la masa y piel"),
            IngredienteReceta("Hojas de plátano", "para forrar", "hojas platano"),
        ],
        pasos=[
            "Mezcla arroz crudo con arvejas, cebolla, ajo, comino, color, sal",
            "Rellena el cerdo con la mezcla, cose bien la abertura",
            "Unta manteca por toda la piel generosamente",
            "Envuelve en hojas de plátano, ata firme",
            "Hornea 6-8 horas a 180°C (o leñera tradicional)",
            "Última hora: sube temp a 220°C para cuerito crujiente",
            "Deja reposar 30 min, destapa, sirve con arepa e insulso",
        ],
        tags=["tradicional", "tolima", "fiesta", "especial", "cuerito", "iconico", "grande"],
    ),

    Receta(
        id="natilla",
        nombre="Natilla Colombiana",
        descripcion="Postre navideño por excelencia: crema de leche, panela, maicena, canela y clavo. Se come con buñuelos",
        categoria="postre",
        tiempo_min=60,
        porciones=12,
        costo_estimado_cop=18000,
        imagen_url=None,
        ingredientes=[
            IngredienteReceta("Leche entera", "3 litros", "leche entera"),
            IngredienteReceta("Panela", "1kg", "panela", notas="rayada o en polvo"),
            IngredienteReceta("Maicena", "200g", "maicena", notas="disuelta en 1 taza leche fría"),
            IngredienteReceta("Canela en rama", "3 unidades", "canela"),
            IngredienteReceta("Clavo de olor", "6 unidades", "clavo"),
            IngredienteReceta("Mantequilla", "100g", "mantequilla"),
            IngredienteReceta("Sal", "1 pizca", "sal"),
            IngredienteReceta("Queso costeño", "200g", "queso costeño", obligatorio=False, notas="rallado, para acompañar"),
        ],
        pasos=[
            "Hierve leche con panela, canela, clavo y sal 10 min",
            "Retira canela y clavo, baja fuego",
            "Añade maicena disuelta poco a poco sin parar de revolver",
            "Cocina 30-40 min revolviendo constante hasta espesar y ver fondo",
            "Incorpora mantequilla, mezcla bien",
            "Vierte en molde/bandeja, deja enfriar y cuajar",
            "Sirve en cuadritos con buñuelos y queso costeño",
        ],
        tags=["tradicional", "navidad", "postre", "dulce", "compartir", "buñuelos"],
    ),

    Receta(
        id="buñuelos",
        nombre="Buñuelos Colombianos",
        descripcion="Bolitas de queso costeño y almidón, fritas hasta doradas, aireadas por dentro. Inseparables de la natilla",
        categoria="postre",
        tiempo_min=40,
        porciones=20,
        costo_estimado_cop=15000,
        imagen_url=None,
        ingredientes=[
            IngredienteReceta("Queso costeño", "500g", "queso costeño", notas="bien seco, rallado"),
            IngredienteReceta("Almidón de maíz/Yucca", "500g", "almidon maiz", notas="tipo Maizena"),
            IngredienteReceta("Huevos AAA", "4 unidades", "huevos AAA"),
            IngredienteReceta("Azúcar", "100g", "azucar"),
            IngredienteReceta("Polvo de hornear", "1 cucharadita", "polvo hornear"),
            IngredienteReceta("Sal", "1 cucharadita", "sal"),
            IngredienteReceta("Aceite vegetal", "para freír", "aceite vegetal"),
        ],
        pasos=[
            "Mezcla queso, almidón, azúcar, polvo de hornear, sal",
            "Añade huevos uno a uno, amasa hasta masa suave y homogénea",
            "Deja reposar 15 min tapada",
            "Forma bolitas de 3-4 cm (crecen al freír)",
            "Fríe en aceite a 160°C (baja temp) 8-10 min, giran solas",
            "Escurre, sirve calientes con natilla",
        ],
        tags=["tradicional", "navidad", "postre", "queso", "crujiente", "natilla"],
    ),

    Receta(
        id="arroz_con_leche",
        nombre="Arroz con Leche Cremoso",
        descripcion="Postre clásico: arroz cocido en leche con canela, clavo, pasas y leche condensada. Frío o tibio",
        categoria="postre",
        tiempo_min=50,
        porciones=8,
        costo_estimado_cop=12000,
        imagen_url=None,
        ingredientes=[
            IngredienteReceta("Arroz blanco", "1 taza", "arroz blanco"),
            IngredienteReceta("Leche entera", "2 litros", "leche entera"),
            IngredienteReceta("Leche condensada", "1 lata (395g)", "leche condensada"),
            IngredienteReceta("Canela en rama", "2 unidades", "canela"),
            IngredienteReceta("Clavo de olor", "4 unidades", "clavo"),
            IngredienteReceta("Pasas", "1/2 taza", "pasas", obligatorio=False, notas="remojadas en ron"),
            IngredienteReceta("Mantequilla", "1 cucharada", "mantequilla"),
            IngredienteReceta("Canela en polvo", "para espolvorear", "canela", obligatorio=False),
        ],
        pasos=[
            "Hierve arroz en 1L agua con canela y clavo 10 min, escurre",
            "En otra olla hierve leche con canela y clavo",
            "Añade arroz, baja fuego, cocina 25 min revolviendo",
            "Incorpora leche condensada, pasas, mantequilla, 5 min más",
            "Retira canela y clavo, sirve en copas",
            "Espolvorea canela en polvo, come tibio o frío",
        ],
        tags=["tradicional", "postre", "cremoso", "reconfortante", "facil", "economico"],
    ),

    Receta(
        id="aguapanela",
        nombre="Aguapanela con Queso",
        descripcion="Bebida caliente de panela con limón y queso derretido. El desayuno/merienda de los campesinos, energética y deliciosa",
        categoria="bebida",
        tiempo_min=15,
        porciones=4,
        costo_estimado_cop=8000,
        imagen_url=None,
        ingredientes=[
            IngredienteReceta("Panela", "500g", "panela", notas="en bloque o polvo"),
            IngredienteReceta("Agua", "2 litros", "agua"),
            IngredienteReceta("Limón", "2 unidades", "limon", notas="jugo"),
            IngredienteReceta("Queso campesino", "200g", "queso campesino", notas="en trozos pequeños"),
            IngredienteReceta("Canela en rama", "1 unidad", "canela", obligatorio=False),
        ],
        pasos=[
            "Hierve agua con panela y canela 10 min hasta disolver",
            "Retira canela, añade jugo de limón",
            "Sirve en tazas, pon queso en cada una",
            "Deja que queso se derrita un poco",
            "Toma caliente, come queso con cuchara",
        ],
        tags=["tradicional", "campesino", "desayuno", "merienda", "caliente", "energetico"],
    ),

    Receta(
        id="cholado",
        nombre="Cholado Valluno",
        descripcion="Postre/bebida del Valle: hielo raspado, frutas, leche condensada, leche en polvo, galletas, salsas. ¡Refrescante y colorido!",
        categoria="postre",
        tiempo_min=20,
        porciones=2,
        costo_estimado_cop=15000,
        imagen_url=None,
        ingredientes=[
            IngredienteReceta("Hielo", "para raspar", "hielo", notas="bloque grande"),
            IngredienteReceta("Mora", "1 taza", "mora", notas="en mermelada o fresca licuada"),
            IngredienteReceta("Mango", "1 unidad", "mango", notas="en cubitos"),
            IngredienteReceta("Banano", "1 unidad", "banano", notas="en rodajas"),
            IngredienteReceta("Piña", "1 taza", "piña", notas="en cubitos"),
            IngredienteReceta("Leche condensada", "1 lata", "leche condensada"),
            IngredienteReceta("Leche en polvo", "1/2 taza", "leche polvo"),
            IngredienteReceta("Galletas María", "6 unidades", "galletas maria", notas="molidas"),
            IngredienteReceta("Salsa de fresa/mora", "al gusto", "salsa fresa"),
            IngredienteReceta("Crema de leche", "opcional", "crema leche", obligatorio=False),
        ],
        pasos=[
            "Raspa hielo en raspador o licuadora (textura nieve)",
            "En copa grande: capa de hielo, frutas, leche condensada",
            "Repite capas: hielo, frutas, leche condensada",
            "Espolvorea leche en polvo y galletas molidas",
            "Riega salsa de fresa/mora por encima",
            "Añade crema de leche si deseas, come inmediato",
        ],
        tags=["vallenato", "refrescante", "colorido", "postre", "helado", "fiesta"],
    ),

    Receta(
        id="lulada",
        nombre="Lulada Vallecaucana",
        descripcion="Bebida tradicional del Valle: lulo licuado con agua, azúcar y hielo. Ácida, refrescante, única",
        categoria="bebida",
        tiempo_min=10,
        porciones=4,
        costo_estimado_cop=10000,
        imagen_url=None,
        ingredientes=[
            IngredienteReceta("Lulos", "8-10 unidades", "lulo", notas="maduros, suaves"),
            IngredienteReceta("Agua", "2 litros", "agua"),
            IngredienteReceta("Azúcar", "al gusto", "azucar", notas="150-200g aprox"),
            IngredienteReceta("Hielo", "abundante", "hielo"),
        ],
        pasos=[
            "Corta lulos por la mitad, saca pulpa con cuchara",
            "Licúa pulpa con agua y azúcar 30 seg (no más, amarga)",
            "Cuela para quitar semillas",
            "Sirve en vasos con mucho hielo",
            "Toma inmediato, no dejes reposar",
        ],
        tags=["vallenato", "refrescante", "acida", "natural", "unica", "bebida"],
    ),

    Receta(
        id="mojarra_frita",
        nombre="Mojarra Frita con Arroz de Coco",
        descripcion="Pescado entero frito hasta crujiente, con arroz de coco, patacones y ensalada. Clásico de la costa Caribe",
        categoria="almuerzo",
        tiempo_min=40,
        porciones=2,
        costo_estimado_cop=45000,
        imagen_url=None,
        ingredientes=[
            IngredienteReceta("Mojarra/tilapia", "2 unidades (500g c/u)", "mojarra", notas="limpias, con corte transversal"),
            IngredienteReceta("Arroz blanco", "2 tazas", "arroz blanco"),
            IngredienteReceta("Leche de coco", "400ml", "leche coco", notas="1 lata"),
            IngredienteReceta("Cebolla cabezona", "1 grande", "cebolla cabezona", notas="para el arroz"),
            IngredienteReceta("Ajo", "2 dientes", "ajo"),
            IngredienteReceta("Plátano verde", "4 unidades", "platano verde", notas="para patacones"),
            IngredienteReceta("Aceite vegetal", "abundante", "aceite vegetal"),
            IngredienteReceta("Sal, pimienta, comino", "al gusto", "sal"),
            IngredienteReceta("Limón", "2 unidades", "limon", notas="para marinada y servir"),
            IngredienteReceta("Ensalada (tomate, cebolla, lechuga)", "al gusto", "tomate riñón", obligatorio=False),
        ],
        pasos=[
            "Marina mojarras con sal, pimienta, comino, limón 15 min",
            "Arroz de coco: sofríe cebolla, ajo, añade arroz, leche de coco + agua, cocina",
            "Fríe mojarras en aceite caliente 8-10 min por lado hasta crujientes",
            "Haz patacones: aplasta plátano, fríe 2 veces",
            "Sirve: mojarra, arroz de coco, patacones, ensalada, limón",
        ],
        tags=["costeño", "caribe", "pescado", "coco", "crujiente", "playa", "verano"],
    ),

    Receta(
        id="pechuga_plancha",
        nombre="Pechuga a la Plancha con Verduras",
        descripcion="Pechuga de pollo jugosa marinada en hierbas, con verduras asadas. Sano, rápido y económico para la semana",
        categoria="almuerzo",
        tiempo_min=25,
        porciones=4,
        costo_estimado_cop=22000,
        imagen_url=None,
        ingredientes=[
            IngredienteReceta("Pechuga de pollo", "4 unidades (800g)", "pollo", notas="aplastadas parejo"),
            IngredienteReceta("Zanahoria", "2 medianas", "zanahoria", notas="en bastones"),
            IngredienteReceta("Calabacín/berenjena", "2 unidades", "zanahoria", obligatorio=False, notas="en rodajas"),
            IngredienteReceta("Pimentón", "1 unidad", "pimenton", notas="en tiras"),
            IngredienteReceta("Cebolla cabezona", "1 grande", "cebolla cabezona", notas="en julianas"),
            IngredienteReceta("Ajo", "3 dientes", "ajo", notas="machacado"),
            IngredienteReceta("Orégano/tomillo", "1 cucharada", "orégano", obligatorio=False),
            IngredienteReceta("Aceite de oliva/vegetal", "3 cucharadas", "aceite vegetal"),
            IngredienteReceta("Limón", "1 unidad", "limon", notas="jugo para marinar"),
            IngredienteReceta("Sal y pimienta", "al gusto", "sal"),
        ],
        pasos=[
            "Marina pechugas: ajo, orégano, limón, aceite, sal, pimienta 20 min",
            "Corta verduras en bastones/rodajas parejos",
            "Calienta plancha/sartén con gota de aceite",
            "Cocina pechugas 5-6 min por lado (no muevas mucho)",
            "En misma plancha asa verduras 8-10 min hasta tiernas-marcadas",
            "Sirve pechuga con verduras, exprime limón encima",
        ],
        tags=["saludable", "rapido", "semana", "proteina", "bajo_grasa", "fit", "economico"],
    ),

    Receta(
        id="sudado_pollo",
        nombre="Sudado de Pollo",
        descripcion="Pollo guisado en su jugo con papa, zanahoria, arvejas y hogao. Suave, rendidor y reconfortante",
        categoria="almuerzo",
        tiempo_min=50,
        porciones=6,
        costo_estimado_cop=35000,
        imagen_url=None,
        ingredientes=[
            IngredienteReceta("Pollo (presas)", "1.5kg", "pollo", notas="muslos, contramuslos"),
            IngredienteReceta("Papa pastusa", "4 medianas", "papa pastusa", notas="en cubitos grandes"),
            IngredienteReceta("Zanahoria", "2 medianas", "zanahoria", notas="en rodajas gruesas"),
            IngredienteReceta("Arvejas", "1 taza", "arvejas"),
            IngredienteReceta("Cebolla cabezona", "1 grande", "cebolla cabezona"),
            IngredienteReceta("Tomate riñón", "2 grandes", "tomate riñón"),
            IngredienteReceta("Ajo", "4 dientes", "ajo"),
            IngredienteReceta("Comino", "1 cucharadita", "comino"),
            IngredienteReceta("Color", "1 cucharadita", "color"),
            IngredienteReceta("Laurel", "2 hojas", "laurel", obligatorio=False),
            IngredienteReceta("Cilantro", "1 manojo", "cilantro", notas="picado, al final"),
            IngredienteReceta("Aceite vegetal", "2 cucharadas", "aceite vegetal"),
        ],
        pasos=[
            "Sella pollo en aceite caliente hasta dorar, retira",
            "En misma olla sofríe cebolla, ajo, tomate, comino, color",
            "Devuelve pollo, añade agua hasta cubrir, hierve",
            "Tapa y cocina 25 min fuego medio",
            "Añade papa, zanahoria, arvejas, laurel, 15 min más",
            "Apaga, añade cilantro, sirve con arroz blanco y aguacate",
        ],
        tags=["tradicional", "reconfortante", "rendidor", "familiar", "economico", "suave"],
    ),

    Receta(
        id="mote_queso",
        nombre="Mote de Queso Costeño",
        descripcion="Sopa cremosa de ñame/maíz con queso costeño, suero y cilantro. Desayuno fuerte de la costa Caribe",
        categoria="desayuno",
        tiempo_min=45,
        porciones=6,
        costo_estimado_cop=28000,
        imagen_url=None,
        ingredientes=[
            IngredienteReceta("Ñame", "1kg", "ñame", notas="pelado en cubos grandes"),
            IngredienteReceta("Queso costeño", "300g", "queso costeño", notas="desmenuzado"),
            IngredienteReceta("Suero costeño", "500ml", "suero costeño", notas="o suero de leche"),
            IngredienteReceta("Cebolla cabezona", "1 grande", "cebolla cabezona"),
            IngredienteReceta("Ajo", "3 dientes", "ajo"),
            IngredienteReceta("Comino", "1 cucharadita", "comino"),
            IngredienteReceta("Cilantro", "1 manojo", "cilantro", notas="picado abundante"),
            IngredienteReceta("Manteca de cerdo", "2 cucharadas", "manteca cerdo", obligatorio=False),
            IngredienteReceta("Sal", "al gusto", "sal"),
        ],
        pasos=[
            "Hierve ñame en agua con sal hasta tierno, aplasta grosero",
            "Sofríe cebolla, ajo, comino en manteca",
            "Añade sofrito al ñame, incorpora suero poco a poco",
            "Cocina 10 min revolviendo, agrega queso, derrite",
            "Apaga, añade cilantro abundante",
            "Sirve caliente con arepa frita o bollo",
        ],
        tags=["costeño", "caribe", "desayuno", "cremoso", "queso", "fuerte", "tradicional"],
    ),
]


# ============================================================
# FUNCIONES DE BÚSQUEDA Y UTILIDAD
# ============================================================

def obtener_todas_recetas() -> list[Receta]:
    return RECETAS_BASE


def obtener_receta_por_id(receta_id: str) -> Optional[Receta]:
    for r in RECETAS_BASE:
        if r.id == receta_id:
            return r
    return None


def buscar_recetas_por_categoria(categoria: str) -> list[Receta]:
    return [r for r in RECETAS_BASE if r.categoria == categoria]


def detectar_intencion_receta(mensaje: str) -> Optional[str]:
    """Detecta si el usuario está pidiendo una receta específica."""
    mensaje_lower = mensaje.lower().replace("ó", "o").replace("á", "a").replace("é", "e").replace("í", "i").replace("ú", "u")

    palabras_clave = {
        "huevos pericos": "huevos_pericos",
        "huevo perico": "huevos_pericos",
        "pericos": "huevos_pericos",
        "calentado": "calentado_paisa",
        "changua": "changua",
        "ajiaco": "ajiaco",
        "sancocho": "sancocho",
        "hamburguesa": "hamburguesa_casera",
        "hamburguesas": "hamburguesa_casera",
        "hamburguer": "hamburguesa_casera",
        "burger": "hamburguesa_casera",
        "patacon": "patacones_hogao",
        "toston": "patacones_hogao",
        "tostón": "patacones_hogao",
        "arepa queso": "arepas_queso",
        "arepa con queso": "arepas_queso",
        "arepas de queso": "arepas_queso",
        "lenteja": "lentejas",
        "arroz pollo": "arroz_pollo",
        "arroz con pollo": "arroz_pollo",
        "pasta bolognesa": "pasta_bolognesa",
        "bolognesa": "pasta_bolognesa",
        "espagueti": "pasta_bolognesa",
        "toston guacamole": "tostones_guacamole",
        "tostones guacamole": "tostones_guacamole",
        "guacamole": "tostones_guacamole",
        "sopa verdura": "sopa_verdur",
        "sopa de verdura": "sopa_verdur",
        "crema verdura": "sopa_verdur",
        "bandeja": "bandeja_paisa",
        "bandeja paisa": "bandeja_paisa",
        "fritanga": "fritanga",
        "empanada": "empanadas",
        "empanadas": "empanadas",
        "tamal": "tamales",
        "tamales": "tamales",
        "lechona": "lechona",
        "natilla": "natilla",
        "buñuelo": "buñuelos",
        "buñuelos": "buñuelos",
        "arroz con leche": "arroz_con_leche",
        "aguapanela": "aguapanela",
        "cholado": "cholado",
        "lulada": "lulada",
        "mojarra": "mojarra_frita",
        "pechuga": "pechuga_plancha",
        "sudado": "sudado_pollo",
        "mote": "mote_queso",
        "mote queso": "mote_queso",
    }

    for palabra, receta_id in palabras_clave.items():
        if palabra in mensaje_lower:
            return receta_id

    return None


def formatear_receta_para_ayuda(receta: Receta) -> str:
    lineas = []
    lineas.append(f"🍳 **{receta.nombre}** ({receta.tiempo_min} min, {receta.porciones} porciones)")
    lineas.append(f"_{receta.descripcion}_\n")
    lineas.append("**🛒 Ingredientes:**")
    for ing in receta.ingredientes:
        oblig = "✅" if ing.obligatorio else "⭕"
        lineas.append(f"  {oblig} **{ing.nombre}** — {ing.cantidad} {('(' + ing.notas + ')') if ing.notas else ''}")
    lineas.append(f"\n**💰 Costo estimado: ~${receta.costo_estimado_cop:,.0f} COP**")
    if receta.tags:
        tags_str = " ".join([f"#{t}" for t in receta.tags])
        lineas.append(f"\n{tags_str}")
    return "\n".join(lineas)


def formatear_pasos_receta(receta: Receta) -> str:
    lineas = ["**👨‍🍳 Preparación:**"]
    for i, paso in enumerate(receta.pasos, 1):
        lineas.append(f"  {i}. {paso}")
    return "\n".join(lineas)


def generar_busquedas_ingredientes(receta: Receta) -> list[str]:
    return [ing.busqueda_catalogo for ing in receta.ingredientes if ing.obligatorio]


def obtener_ingredientes_principales(receta: Receta) -> list[str]:
    return [ing.nombre for ing in receta.ingredientes if ing.obligatorio]