
const formulario = document.getElementById("formulario");
const consulta = document.getElementById("consulta");
const resultado = document.getElementById("resultado");

// Formulario del leaderboard
const formularioLeaderboard = document.getElementById(
    "formularioLeaderboard"
);
const consultaLeaderboard = document.getElementById(
    "consultaLeaderboard"
);

// Navegación
const btnEjercicios = document.getElementById("btnEjercicios");
const btnLeaderboard = document.getElementById("btnLeaderboard");

const seccionEjercicios = document.getElementById("seccionEjercicios");
const seccionLeaderboard = document.getElementById("seccionLeaderboard");

const resultadosLeaderboard = document.getElementById(
    "resultadosLeaderboard"
);

// --------------------------------------------------
// NAVEGACIÓN
// --------------------------------------------------

btnEjercicios.addEventListener("click", () => {
    seccionEjercicios.hidden = false;
    seccionLeaderboard.hidden = true;

    btnEjercicios.classList.add("activo");
    btnLeaderboard.classList.remove("activo");

    btnEjercicios.setAttribute("aria-pressed", "true");
    btnLeaderboard.setAttribute("aria-pressed", "false");
});

btnLeaderboard.addEventListener("click", () => {
    seccionEjercicios.hidden = true;
    seccionLeaderboard.hidden = false;

    btnLeaderboard.classList.add("activo");
    btnEjercicios.classList.remove("activo");

    btnLeaderboard.setAttribute("aria-pressed", "true");
    btnEjercicios.setAttribute("aria-pressed", "false");
});

// --------------------------------------------------
// BUSCAR EJERCICIOS: ENDPOINT EXISTENTE
// --------------------------------------------------

formulario.addEventListener("submit", async (evento) => {
    evento.preventDefault();

    const texto = consulta.value.trim();

    if (!texto) return;

    resultado.textContent = "Buscando ejercicios...";

    try {
        const respuesta = await fetch("/buscar", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({ texto })
        });

        const datos = await respuesta.json();

        if (!respuesta.ok) {
            throw new Error(
                datos.detail || "Error al buscar ejercicios."
            );
        }

        if (!Array.isArray(datos.resultados)) {
            throw new Error("La respuesta del servidor no es válida.");
        }

        resultado.replaceChildren();

        if (datos.resultados.length === 0) {
            resultado.textContent = "No se encontraron ejercicios.";
            return;
        }

        datos.resultados.forEach((ejercicio, indice) => {
            const tarjeta = document.createElement("article");
            tarjeta.className = "ejercicio";

            const titulo = document.createElement("h2");
            titulo.textContent = `${indice + 1}. ${ejercicio.tema}`;

            const enunciado = document.createElement("p");
            enunciado.textContent = ejercicio.enunciado;

            const solucion = document.createElement("p");
            solucion.textContent = `Solución: ${ejercicio.solucion}`;

            tarjeta.append(titulo, enunciado, solucion);
            resultado.appendChild(tarjeta);
        });

    } catch (error) {
        console.error(error);
        resultado.textContent =
            error.message || "No se ha podido realizar la búsqueda.";
    }
});

// --------------------------------------------------
// LEADERBOARD: CONSULTA CON OLLAMA Y SQL SERVER
// --------------------------------------------------

formularioLeaderboard.addEventListener("submit", async (evento) => {
    evento.preventDefault();

    const texto = consultaLeaderboard.value.trim();

    if (!texto) return;

    resultadosLeaderboard.replaceChildren();

    const cargando = document.createElement("p");
    cargando.className = "mensaje-inicial";
    cargando.textContent = "Interpretando la pregunta y consultando SQL Server...";
    resultadosLeaderboard.appendChild(cargando);

    const boton = formularioLeaderboard.querySelector(
        'button[type="submit"]'
    );

    if (boton) {
        boton.disabled = true;
    }

    try {
        const respuesta = await fetch("/leaderboard/buscar", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({ texto })
        });

        const datos = await respuesta.json();

        if (!respuesta.ok) {
            throw new Error(
                datos.detail || "No se ha podido consultar el leaderboard."
            );
        }

        resultadosLeaderboard.replaceChildren();

        // Mensaje devuelto por el backend
        if (datos.mensaje) {
            const mensaje = document.createElement("p");
            mensaje.className = "mensaje-inicial";
            mensaje.textContent = datos.mensaje;
            resultadosLeaderboard.appendChild(mensaje);
        }

        // Si Qwen determina que la petición no puede responderse
        if (datos.sql === null) {
            if (!datos.mensaje) {
                resultadosLeaderboard.textContent =
                    "No se ha podido generar una consulta para esta petición.";
            }
            return;
        }

        if (!Array.isArray(datos.resultados)) {
            throw new Error("La respuesta del servidor no es válida.");
        }

        if (datos.resultados.length === 0) {
            const sinResultados = document.createElement("p");
            sinResultados.textContent =
                "No se han encontrado resultados para esta consulta.";
            resultadosLeaderboard.appendChild(sinResultados);
            return;
        }

        // Construir una tabla con los resultados recibidos
        const contenedorTabla = document.createElement("div");
        contenedorTabla.className = "tabla-leaderboard";

        const tabla = document.createElement("table");
        tabla.className = "tabla-resultados";

        const encabezado = document.createElement("thead");
        const filaEncabezado = document.createElement("tr");

        const columnas = Object.keys(datos.resultados[0]);

        const nombresColumnas = {
            id_ejercicio: "ID ejercicio",
            nombre: "Usuario",
            bloque: "Bloque",
            tiempo: "Tiempo (s)"
        };

        columnas.forEach((columna) => {
            const th = document.createElement("th");
            th.scope = "col";
            th.textContent = nombresColumnas[columna] || columna;
            filaEncabezado.appendChild(th);
        });

        encabezado.appendChild(filaEncabezado);

        const cuerpo = document.createElement("tbody");

        datos.resultados.forEach((fila) => {
            const tr = document.createElement("tr");

            columnas.forEach((columna) => {
                const td = document.createElement("td");
                const valor = fila[columna];

                if (columna === "tiempo" && valor !== null) {
                    td.textContent = `${valor} s`;
                } else if (valor === null || valor === undefined) {
                    td.textContent = "—";
                } else {
                    td.textContent = String(valor);
                }

                tr.appendChild(td);
            });

            cuerpo.appendChild(tr);
        });

        tabla.append(encabezado, cuerpo);
        contenedorTabla.appendChild(tabla);
        resultadosLeaderboard.appendChild(contenedorTabla);

    } catch (error) {
        console.error(error);

        resultadosLeaderboard.replaceChildren();

        const mensajeError = document.createElement("p");
        mensajeError.className = "mensaje-error";
        mensajeError.textContent =
            error.message || "No se ha podido consultar el leaderboard.";

        resultadosLeaderboard.appendChild(mensajeError);

    } finally {
        if (boton) {
            boton.disabled = false;
        }
    }
});
