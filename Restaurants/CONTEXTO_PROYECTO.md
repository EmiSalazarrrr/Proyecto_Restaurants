# Contexto del Proyecto — Restaurants
> Última actualización: sesión 2 (rama Visual)

## Rutas clave
```
Proyecto:   C:\Users\DELL\OneDrive\Documentos\ProyectoRestaurants\Proyecto_Restaurants\
App Django: Restaurants/
Templates:  Restaurants/templates/
Static CSS: Restaurants/static/css/performance.css
Vistas:     Restaurants/config/views.py
URLs:       Restaurants/config/urls.py
Modelos:    Restaurants/apps/*/models.py
```

## Arquitectura general
- **Framework**: Django (Python)
- **Templates**: cada `.html` es independiente — sin herencia de base template
- **Fuentes**: DM Sans (cuerpo) + DM Mono (monoespaciado) — Google Fonts con preload
- **Color acento admin**: `#D8AE48` (dorado)
- **Color acento cliente**: `#014BAA` / `#307FE2` (azul)
- **Chart.js**: `4.4.1` desde `cdnjs.cloudflare.com` — usado en `menu_admin.html` y `promociones.html`

---

## Templates y su estado

### Admin (login requerido — rol admin)
| Template | Estado |
|---|---|
| `menu_admin.html` | ✅ Dark mode + Gráfica barras mejorada + Tendencias + Selector rango |
| `lista_tickets.html` | ✅ Dark mode |
| `alimentos_bebidas.html` | ✅ Dark mode |
| `promociones.html` | ✅ Dark mode + Donut chart con colores dinámicos |
| `restricciones.html` | ✅ Dark mode |
| `metricas.html` | ✅ Dark mode |
| `atender_mesa.html` | ✅ Dark mode |

### Cliente
| Template | Estado |
|---|---|
| `menu_cliente.html` | ✅ Dark mode (merge resuelto) + animaciones |
| `historial.html` | ❌ Sin dark mode aún |

### Auth
| Template | Estado |
|---|---|
| `login.html` | ✅ Animación cinematográfica completa |
| `registro.html` | ✅ Card reveal con blur |

---

## Sistema de Dark Mode

### Patrón estándar (todos los admin templates)
```html
<!-- 1. Anti-flash — primer <script> en <head> después de <meta charset> -->
<script>!function(){var t=localStorage.getItem('theme');t&&document.documentElement.setAttribute('data-theme',t)}();</script>
```

```css
/* 2. Variables dark mode — SIEMPRE inline en el template, nunca en performance.css (caché) */
html[data-theme="dark"] {
    --bg: #111827; --card-bg: #1a2035; --card-border: rgba(255,255,255,0.07);
    --text-primary: #e2ddd5; --text-secondary: #a08870; --text-muted: #6e5e52;
    --sidebar-bg: #090d14; --accent: #D8AE48; --accent-dim: rgba(216,174,72,0.11);
    --success: #4cc970; --success-dim: rgba(76,201,112,0.10);
    --danger: #f07a7a; --danger-dim: rgba(240,122,122,0.08);
}
```

```html
<!-- 3. Botón en sidebar -->
<div class="sidebar-bottom">
    <button class="btn-theme" id="theme-toggle" onclick="toggleTheme()">🌙 Modo oscuro</button>
    <a class="btn-logout" href="{% url 'logout' %}">Cerrar sesion</a>
</div>
```

```css
/* 4. CSS del botón — inline (no en performance.css) */
.sidebar-bottom { margin-top: auto; padding: 20px 24px; border-top: 1px solid var(--card-border); display: flex; flex-direction: column; gap: 10px; }
.btn-theme { display: flex; align-items: center; gap: 8px; justify-content: center; width: 100%; background: transparent; border: 1px solid rgba(244,240,232,0.12); border-radius: 8px; padding: 9px 14px; color: rgba(244,240,232,0.65); cursor: pointer; font: 500 13px "DM Sans", sans-serif; transition: all 0.15s; line-height: 1; white-space: nowrap; }
.btn-theme:hover { border-color: var(--accent, #D8AE48); color: var(--accent, #D8AE48); }
```

```javascript
// 5. JS del toggle — al final del <script>
function toggleTheme() {
    var dark = document.documentElement.getAttribute('data-theme') === 'dark';
    var next = dark ? 'light' : 'dark';
    document.documentElement.setAttribute('data-theme', next);
    localStorage.setItem('theme', next);
    updateThemeBtn();
}
function updateThemeBtn() {
    var btn = document.getElementById('theme-toggle');
    if (!btn) return;
    var dark = document.documentElement.getAttribute('data-theme') === 'dark';
    btn.textContent = dark ? '☀️ Modo claro' : '🌙 Modo oscuro';
}
updateThemeBtn();
```

### Regla crítica sobre colores inline vs CSS class
**Nunca usar `style="color:..."` inline en elementos que deben cambiar con dark mode.**
El CSS `!important` del stylesheet puede ganar sobre inline styles, pero es frágil.
Usar clases CSS con overrides de dark mode explícitos. Ejemplo del proyecto:

```css
/* ✅ Correcto — clase con override de dark mode */
.stat-card--alert .stat-value { color: #1a3acc; }
html[data-theme="dark"] .stat-card--alert .stat-value { color: #7B9FFF !important; }
```
```html
<!-- En el template -->
<article class="stat-card {% if canjeados_pendientes %}stat-card--alert{% endif %}">
```

---

## Dashboard Admin — menu_admin.html

### Gráfica de barras (ventas 7/14/30 días)
- **Canvas**: `<canvas id="ventas-chart">`
- **Chart.js**: instancia guardada en `window._ventasChart`
- **Gradiente**: plugin `barGradient` que crea `createLinearGradient` antes de cada dibujado
  - Arriba: `rgba(201,151,43,0.55)` → Abajo: `rgba(201,151,43,0.04)`
- **Borde**: `borderWidth: { top: 2, right: 0, bottom: 0, left: 0 }`, `borderColor: '#C9972B'`
- **Bordes redondeados**: `borderRadius: { topLeft: 4, topRight: 4 }`
- **Tooltip**: custom CSS (`#bar-tooltip`), no el nativo de Chart.js
- **Datos**: `{{ labels|safe }}` y `{{ values|safe }}` desde Django (JSON)
- **Colores de ticks**: dinámicos según tema — funciones `chartTickColor()` y `chartGridColor()`
  - Modo claro: `#5C4A3A` (oscuro, buen contraste sobre fondo crema)
  - Modo oscuro: `#a09080` (claro, buen contraste sobre fondo oscuro)
- **Al cambiar tema**: `toggleTheme()` llama `_ventasChart.update('none')` para refrescar colores

### Selector de rango (7 / 14 / 30 días)
- **Botones**: `.range-btn` con `data-dias` attribute, `.range-btn.active` tiene fondo dorado claro
- **Endpoint**: `GET /dashboard/ventas-data/?dias=N` → JSON `{"labels": [...], "values": [...]}`
- **Fetch**: al click, actualiza `_ventasChart.data.labels`, `.data.datasets[0].data`, luego `.update()`
- **Carga inicial**: usa datos de Django (sin fetch extra) — 7 días por defecto, botón `active`

### Tendencias en tarjetas de stats
**Vista (views.py)**:
```python
def _trend(hoy, ayer):
    hoy, ayer = float(hoy), float(ayer)
    if ayer == 0:
        return ("up", None) if hoy > 0 else ("flat", None)
    pct = (hoy - ayer) / ayer * 100
    if abs(pct) < 0.05:
        return "flat", None
    return ("up" if pct > 0 else "down"), round(abs(pct), 1)
```
Contexto que pasa: `ventas_trend_dir`, `ventas_trend_pct`, `tickets_trend_dir`, etc.

**Template**:
```html
{% if ventas_trend_dir == 'up' %}
    <div class="stat-trend trend-up">↑ {% if ventas_trend_pct %}{{ ventas_trend_pct }}%{% else %}Nuevo{% endif %} vs ayer</div>
{% elif ventas_trend_dir == 'down' %}
    <div class="stat-trend trend-down">↓ {{ ventas_trend_pct }}% vs ayer</div>
{% else %}
    <div class="stat-trend trend-flat">— Sin cambio vs ayer</div>
{% endif %}
```
CSS: `.trend-up { color: #22c55e }` / `.trend-down { color: #ef4444 }` / `.trend-flat { color: var(--text-muted) }`
Dark mode: `.trend-up { color: #4ade80 }` / `.trend-down { color: #f87171 }`

---

## Gráfica donut en promociones.html
El número central del donut se dibuja con canvas API — hay que leer el tema en `afterDraw`:
```javascript
window._donutChart = new Chart(...);  // guardar referencia

// En el plugin:
afterDraw(chart) {
    const isDark = document.documentElement.getAttribute('data-theme') === 'dark';
    ctx.fillStyle = isDark ? '#e2ddd5' : '#0D1E3B';   // número
    ctx.fillStyle = isDark ? '#6e5e52' : '#9B8B7A';   // texto "total"
}

// En toggleTheme():
if (window._donutChart) window._donutChart.update();
```
**Lo mismo aplica para el donut de menu_admin.html** (número "tickets" en el centro).

---

## Animaciones implementadas

### login.html — Cinematic slide-in
```css
body { display: flex; overflow: hidden; }   /* NO grid */
.panel { width: 0; flex-shrink: 0; overflow: hidden; opacity: 0;
    transition: width 0.95s cubic-bezier(0.4,0,0.2,1), opacity 0.65s ease 0.5s; }
.panel.open { width: 440px; opacity: 1; }
```
```javascript
// JS: después de 1500ms (desktop) / 1200ms (mobile) / 400ms (reduced-motion):
panel.classList.add('open');
```
Mobile: usa `transform: translateY(44px → 0)` en vez de `width`.

### registro.html — Card reveal con blur
```css
.card { animation: cardReveal 1.1s cubic-bezier(0.22,0.61,0.36,1) 0.55s both; }
@keyframes cardReveal {
    from { opacity: 0; transform: translateY(52px) scale(0.93); filter: blur(6px); }
    60%  { filter: blur(1px); }
    to   { opacity: 1; transform: translateY(0) scale(1); filter: blur(0px); }
}
```

### Regla general de animaciones
- Siempre `opacity: 0` + `animation: ... forwards` en el from
- Usar `fill: both` para que el elemento esté invisible antes de que arranque la animación
- **NUNCA animar `grid-template-columns` con `fr`** — no es interpolable. Usar `width` + `display: flex`

---

## performance.css — Bugs corregidos (importante)
Archivo: `Restaurants/static/css/performance.css`
⚠️ Este archivo tiene caché agresiva del browser — todo CSS dinámico va inline en templates.

**Fix 1 — prefers-reduced-motion** (era `0.01ms`, mataba todas las animaciones):
```css
@media (prefers-reduced-motion: reduce) {
    *, *::before, *::after {
        animation-duration: 0.25s !important;
        animation-delay: 0s !important;
        transition-duration: 0.25s !important;
        transition-delay: 0s !important;
    }
}
```

**Fix 2 — Mobile body layout** (era `display: grid`, rompía el flex del login):
```css
@media (max-width: 900px) {
    body:has(.hero):has(.panel) {
        display: flex !important;
        flex-direction: column !important;
    }
}
```

---

## views.py — Funciones relevantes

```python
# Helpers
def _build_daily_series(desde, hasta, queryset)  # → (labels, data)
def _build_monthly_series(desde, hasta, queryset) # → (labels, data)
def _trend(hoy, ayer)                             # → ('up'|'down'|'flat', pct|None)

# Vistas
def menu_admin_view(request)    # Dashboard — calcula hoy + ayer + tendencias
def ventas_data_view(request)   # AJAX: GET /dashboard/ventas-data/?dias=N → JSON
def metricas_view(request)      # Métricas con filtro de periodo
```

## URLs relevantes
```python
path('menu-admin/',               views.menu_admin_view,   name='menu_admin')
path('dashboard/ventas-data/',    views.ventas_data_view,  name='ventas_data')
path('metricas/',                 views.metricas_view,     name='metricas')
path('promociones/',              promociones_views.promociones_view, name='promociones')
```

---

## Reglas del proyecto (no romper)

1. **CSS de dark mode siempre inline** en el template — nunca en `performance.css` (caché)
2. **Anti-flash script** = primer `<script>` en `<head>` justo después de `<meta charset>`
3. **Sin base template**: cada HTML es independiente — replicar cambios comunes en todos
4. **Inline styles y dark mode no se llevan bien** — usar clases CSS con selectores específicos
5. **Canvas/Chart.js no responde a CSS dark mode** — leer el tema en JS y actualizar con `.update()`
6. **Chart.js guardado en `window._nombreChart`** para poder hacer `.update()` desde toggleTheme

---

## Modelos principales (referencia rápida)
- `Ticket`: `id_ticket`, `nombre_usuario`, `fecha`, `precio_final`, `pagado` (bool), `canjeado` (0/1/-1)
- `Alimentosbebidas`: `nombre`, `descripcion`, `costo`, activo
- `Promocion`: `nombre`, `descripcion`, `porcentaje_a_reducir`, `id_restriccion`, `activo`
- `Cliente`: relacionado con usuario Django
- `canjeado=-1` = cancelado, `canjeado=0` = sin canjear, `canjeado=1` = canjeado pendiente de cobro
