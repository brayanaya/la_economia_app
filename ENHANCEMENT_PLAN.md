# Plan de Mejora: Economía Aya - Asistente Inteligente de Compras

## Visión General
Transformar el asistente RAG actual en **Economía Aya**: una IA conversacional, intuitiva y útil que actúa como una amiga experta en compras y cocina colombiana.

---

## 1. Mejora del System Prompt (Backend)

### Prompt Actual (básico)
- Responde breve, amable
- Solo productos del contexto
- No inventa nada

### Prompt Objetivo (Economía Aya)
```
Eres "Aya", la asistente personal de compras de La Economía Aya (supermercado en Neiva, Huila).
Tu personalidad: cercana, experta, práctica, honesta - como una amiga que sabe de compras y cocina.

PRINCIPIOS FUNDAMENTALES:
1. EXPLICA EL POR QUÉ: Nunca digas solo "recomiendo X". Di: "Te recomiendo X porque [razón real: reseñas, popularidad, ingredientes, relación calidad-precio, etc.]"
2. SÉ ESPECÍFICA: Usa detalles concretos del producto (marca, peso, precio, características).
3. AYUDA A COCINAR: Si piden recetas/desayunos, da la receta completa CON ingredientes listados y sus precios estimados.
4. VISUAL: Menciona que puede ver las imágenes de los productos/ingredientes.
5. HONESTA: Si no hay stock o no es buena opción, dilo. "Este café está agotado en tu sede, pero hay uno similar..."
6. COLOMBIANA: Usa términos locales (arepa, huevos pericos, changua, calentado, tinto, etc.)
7. CONSCIENTE DEL BOLSILLO: Menciona precios, ofertas, alternativas más económicas.

FORMATO DE RESPUESTA IDEAL:
- Saludo natural
- Recomendación principal CON razón
- Opción alternativa (si aplica)
- Para recetas: lista ingredientes con "🥚 Huevos - $X" "🧅 Cebolla - $Y" etc.
- Pregunta de seguimiento útil: "¿Te lo agrego al carrito?" "¿Quieres que te diga cómo prepararlo?"

EJEMPLOS DE TU TONO:
❌ "Recomiendo Café Sello Rojo"
✅ "Para tu tinto de las mañanas, el **Café Sello Rojo 500g ($18.500)** es mi favorito: tiene 4.8 estrellas, la gente dice que 'huele a finca cafetera' y es 100% grano colombiano. Si buscas algo más suave, el **Águila Roja 250g ($9.800)** también está rico y rinde más. ¿Cuál te llevo?"

❌ "Aquí tienes los ingredientes para huevos pericos"
✅ "¡Huevos pericos con arepa! Clásico desayuno paisa 😋 Aquí tienes todo lo que necesitas:

🥚 **Huevos AAA x12** - $14.900 (necesitas 3)
🧅 **Cebolla cabezona** - $3.200/kilo (media cebolla)
🍅 **Tomate riñón** - $4.500/kilo (1 grande)
🌽 **Arepa de maíz x10** - $6.800 (2 arepas)
🧈 **Mantequilla** - $8.900 (opcional, para la arepa)

**Total estimado: ~$22.000** (te sobra para toda la semana)
¿Te armo el carrito con estos? ¿O prefieres que te explique el paso a paso?"
```

---

## 2. Nuevas Capacidades Necesarias

### A. Modo Recetas / "¿Qué cocino hoy?"
- Base de conocimiento de recetas colombianas populares
- Mapeo receta → ingredientes (productos en catálogo)
- Cálculo de costo estimado por porción
- Instrucciones de preparación breves

### B. Conocimiento Enriquecido de Productos
Agregar a productos (en BD o en embeddings):
- `rating_promedio` (1-5)
- `num_resenas` 
- `etiquetas`: ["natural", "organico", "bajo_azucar", "sin_gluten", "vegano", "local", "tradicional"]
- `descripcion_larga` con beneficios, uso sugerido
- `ingredientes_principales` (para alimentos procesados)
- `alergenos`

### C. Memoria de Conversación (contexto)
- Recordar preferencias del usuario en la sesión
- "La última vez compraste café Sello Rojo, ¿repites?"
- Historial de recetas consultadas

### D. Sugerencias Proactivas
- "Como compraste huevos y arepas, ¿quieres tomate y cebolla para pericos?"
- "Es fin de semana, ¿te ayudo con el mercado de la semana?"

---

## 3. Cambios en Frontend

### ChatAgente.tsx - Mejoras Visuales
1. **Tarjetas de receta** con grid de ingredientes + imágenes
2. **Indicador de "Aya está pensando..."** más natural
3. **Botones de acción rápida**: "Agregar todo al carrito", "Ver receta", "Alternativas"
4. **Chips de categoría**: "Desayunos", "Cenas rápidas", "Saludable", "Presupuesto"
5. **Modo "Cocina conmigo"** - paso a paso con timer

### Nueva Componente: RecetaCard.tsx
```tsx
interface RecetaCardProps {
  nombre: string;
  descripcion: string;
  ingredientes: { producto: Producto; cantidad: string; obligatorio: boolean }[];
  tiempoMin: number;
  porciones: number;
  costoEstimado: number;
  pasos: string[];
}
```

---

## 4. Arquitectura de Datos Propuesta

### Nuevas Tablas (Opcional - puede ser en prompt/context)
```sql
-- Recetas base (precargadas)
CREATE TABLE recetas (
  id UUID PRIMARY KEY,
  nombre VARCHAR(200),
  descripcion TEXT,
  tiempo_min INT,
  porciones INT,
  categoria VARCHAR(50), -- 'desayuno', 'almuerzo', 'cena', 'snack'
  imagen_url TEXT,
  instrucciones TEXT[],
  costo_estimado_cop DECIMAL(12,2)
);

-- Ingredientes de receta (link a productos)
CREATE TABLE receta_ingredientes (
  receta_id UUID REFERENCES recetas(id),
  producto_id UUID REFERENCES productos(id),
  cantidad VARCHAR(50), -- "3 unidades", "200g", "1 taza"
  obligatorio BOOLEAN DEFAULT true,
  notas TEXT -- "picado fino", "opcional para decorar"
);
```

---

## 5. Plan de Implementación por Fases

### Fase 1: Prompt Maestro + Few-Shot (Inmediato - Alto Impacto)
- [ ] Reescribir `generar_respuesta_agente` con prompt completo de Aya
- [ ] Agregar 5-10 ejemplos few-shot en el prompt
- [ ] Probar con consultas reales

### Fase 2: Conocimiento de Recetas (1-2 días)
- [ ] Crear JSON/array de recetas colombianas populares (15-20)
- [ ] Función `detectar_intencion_receta(mensaje)` 
- [ ] Función `buscar_ingredientes_receta(nombre_receta)` → busca productos en catálogo
- [ ] Integrar en flujo de respuesta

### Fase 3: Frontend Visual para Recetas (1-2 días)
- [ ] Componente `RecetaCard` con grid de ingredientes + imágenes
- [ ] Botón "Agregar todos los ingredientes al carrito"
- [ ] Vista paso a paso de preparación

### Fase 4: Memoria y Personalización (Opcional)
- [ ] Contexto de sesión (preferencias, alergias, presupuesto)
- [ ] Sugerencias basadas en historial

---

## 6. Recetas Iniciales Prioritarias (Colombianas)

| Receta | Ingredientes Clave | Categoría |
|--------|-------------------|-----------|
| Huevos pericos con arepa | Huevos, cebolla, tomate, arepa, mantequilla | Desayuno |
| Calentado paisa | Arroz, frijoles, carne, plátano, huevo, arepa | Almuerzo |
| Changua | Leche, huevo, cebolla larga, pan, queso | Desayuno |
| Ajiaco | Pollo, 3 papas, mazorca, guasca, alcaparras, crema | Almuerzo |
| Sancocho | Carne, yuca, plátano, papa, mazorca, cilantro | Almuerzo |
| Patacones con hogao | Plátano verde, tomate, cebolla, ajo, comino | Acompañamiento |
| Arepas de queso | Arepa, queso costeño, mantequilla | Desayuno/Snack |
| Lentejas | Lentejas, zanahoria, papa, chorizo, cilantro | Almuerzo |
| Arroz con pollo | Arroz, pollo, arvejas, zanahoria, ajo, color | Almuerzo |
| Pasta bolognesa | Pasta, carne molida, tomate, cebolla, ajo, laurel | Cena |
| Tostones con guacamole | Plátano, aguacate, limón, cebolla, cilantro | Snack |
| Sopa de verduras | Zanahoria, papa, apio, cebolla, cilantro, caldo | Cena ligera |

---

## 7. Métricas de Éxito

- **Tasa de conversión chat→carrito**: >30%
- **Satisfacción usuario** (encuesta post-chat): >4.5/5
- **Consultas resueltas sin escalar**: >85%
- **Tiempo promedio respuesta**: <3 segundos
- **Uso de "recetas"**: >40% de sesiones

---

## 8. Próximos Pasos Inmediatos

1. **Actualizar `app/services/agente.py`** con el nuevo system prompt maestro
2. **Agregar ejemplos few-shot** reales de conversaciones ideales
3. **Crear `app/services/recetas.py`** con base de conocimiento de recetas
4. **Modificar `agente_chat` endpoint** para detectar intención de receta
5. **Actualizar `ChatAgente.tsx`** para renderizar recetas bonitas

---

## Notas Técnicas

- **No requiere reentrenar modelo**: Todo se logra con prompt engineering + contexto estructurado
- **Compatible con Ollama actual**: qwen2.5:7b maneja bien prompts largos en español
- **Escalable**: Cuando migren a modelo mayor (Llama 3.1 70B, GPT-4o), el prompt sigue funcionando
- **Costo cero**: Todo local, sin API keys externas