#import os
#import sys
import time
import uuid
import math
import openai
import tiktoken
import streamlit as st
import reveal_slides as rs
import streamlit_tags as stt
import https://github.com/vhugohh/ChatPardyGPT/blob/main/functions
from io import BytesIO

num_intro_slides = 3

if 'markdown' not in st.session_state:
    st.session_state.markdown = ""
if 'reveal' not in st.session_state:
    st.session_state.reveal = "new-start"
if 'tokens' not in st.session_state:
    st.session_state.tokens = 0
if 'delta' not in st.session_state:
    st.session_state.delta = 0
if 'lastdelta' not in st.session_state:
    st.session_state.lastdelta = 0
if 'answerfiletxt' not in st.session_state:
    st.session_state.answerfiletxt = ""

## OpenAI API Credentials setup ====================================================
# Openai local configuration

with st.sidebar:
    st.markdown("## Configuración")
    with st.expander("Credenciales OpenAI API"):
        default_openai_key = "OpenAIKey"
        default_openai_org = "organization"
        if openai.api_key and openai.organization:
            default_openai_key = openai.api_key
            default_openai_org = openai.organization
        openai_key = st.text_input("Key", type="password", value=default_openai_key)
        openai_org = st.text_input("Organization", type="password", value=default_openai_org)
        if openai_org and openai_key:
            openai.organization = openai_org
            openai.api_key = openai_key
            try:
                openai.Model.list()
                st.success("Credenciales OpenAI API registradas con éxito!!!")
            except:
                st.error("Credenciales OpenAI API Inválidas!")

if openai_key == "" or openai_org == "":
    st.warning(":arrow_left: Proporcionar credenciales OpenAI: Key y Organization en la barra lateral.")

## App setup ========================================================================
with st.sidebar:
    with st.expander("Configuración"):
        school_level = st.selectbox('Seleccione el Nivel escolar para las preguntas de la trivia',('Primaria', 'Secundaria', 'Bachillerato'))
        if school_level == 'Secundaria':
            school_year = st.selectbox('Seleccione el Año escolar para las preguntas de la trivia',('Primero', 'Segundo', 'Tercero'))
        else:
            school_year = st.selectbox('Seleccione el Año escolar para las preguntas de la trivia',('Primero', 'Segundo', 'Tercero', 'Cuarto', 'Quinto', 'Sexto'))
        ##request_delay = st.number_input("Pausa entre solicitudes a la API para evitar tasa limite de peticiones (segundos)", min_value=0.0, max_value=5.0, value=1.0, step=0.1)
        request_delay = 1.0		
        multiplier = st.number_input("Multiplicador de montos en el juego", min_value=1, max_value=8, value=1, step=1)
        question_timer = st.number_input("Tiempo máximo de los jugadores para contestar (segundos)", min_value=0, max_value=60, value=10, step=1)

## Main App ========================================================================
slide_markdown = r"""<section data-markdown="" data-separator-vertical="^--$" data-separator-notes="^Answer:" >
<script type="text/template">
## [Bienvenidos a AI Trivia School!](#/1)"""

slide_markdown_close = r"""
</script>
</section>
<script type="application/javascript">
    function findLink(el) {
        if (el.tagName == 'A' && el.href) {
            return el;
        } else if (el.parentElement) {
            return findLink(el.parentElement);
        } else {
            return null;
        }
    };

    function callback(e) {
        const link = findLink(e.target);
        if (link == null) { return; }
        e.preventDefault();
        // Do stuff here
        link.classList.add("clicked");
    };

    document.addEventListener('click', callback, false);
</script>
"""

st.image("https://upload.wikimedia.org/wikipedia/commons/d/da/Trivia_1.png", width=400)
st.title("¡AI Trivia School! - (ChatPardyGPT)")
st.subheader("Un juego de trivia estilo Jeopardy producido mediante la inteligencia artificial generativa ChatGPT para apoyar la Gamificación en las escuelas")

with st.expander("Instrucciones y tips"):
    st.markdown("""**Esta app permite generar un juego de trivia estilo Jeopardy con preguntas y respuestas.** 
- _Comienza seleccionando del panel izquierdo el nivel educativo "Primaria", "Secundaria" o "Bachillerato" y el grado académico._
- _Posteriormente escribir 6 temas de tu elección para ser usados como categorias._
- _Despues de introducir las 6 categorias se habilitara el boton Juego Nuevo. Da Click en él para generar un nuevo juego (la generación del juego podría tardar un par de minutos)._
- _El juego se genera como una serie de diapositivas en las que se navegará dando click en el texto **amarillo**_
- _Para activar el modo de Pantalla Completa dar click en cualquier parte de la diapositiva y presionar la letra `F` en el teclado._
- _Revisar el panel izquierdo para otras configuraciones._""")

categories = stt.st_tags(label="Introduce 6 categorías de trivia", suggestions="Introduce una categoría y presiona enter", maxtags=6, key="categories")
cola, colb, colc = st.columns([1.1,4.6,1])
if categories:
    if cola.button("Juego Nuevo", disabled=len(categories) < 6):
        token_count_at_start = st.session_state.tokens
        with st.spinner("Generando el juego..."):
            intro_offset = num_intro_slides
            slide_markdown += "\n---\n"+ r"""<!-- .slide: data-transition="convex" -->""" + "\n ## [Las categorias son ... ](#/2) "
            for category in categories:
                slide_markdown += f"\n---\n"+ r"""<!-- .slide: data-transition="convex" -->""" + f"\n ## [{category.upper()}](#/{intro_offset})"
                intro_offset += 1
            ##slide_markdown += "\n---\n" + r"""<!-- .slide: data-background-image="https://cdn.vox-cdn.com/thumbor/wEcBsqpKaKmrw6TWYNIDQfOPENk=/172x118:2400x1232/fit-in/1200x600/cdn.vox-cdn.com/uploads/chorus_asset/file/19577016/jeopardy_02.jpg" data-background-size="118%" data-background-position="20%" -->""" + "\n"
            slide_markdown += "\n---\n" + r"""<!-- .slide: data-background-image="https://parade.com/.image/t_share/MTkwNTgxMTE3NzUxOTkzNDY5/jeopardy-board.jpg" data-background-size="100%" data-background-position="20%" -->""" + "\n"
			## Score
            #slide_markdown += f"Team 1: $5000                                       Team 2: $1500" + "\n"
            #slide_markdown += "<H2 align=left>TEAM 1: $5000</H2> <H2 align=right>TEAM 2: $2000</H2>" + "\n"
			
            slide_markdown += "|"
            jeopardy_set = []
            loops_to_time = 1
            loop_count = 1
            timer_start = time.time()
            for category in categories:
                slide_markdown += f" {category.upper()} |"
                qa_array = functions.retry_get_jeopardy_trivia(category, school_year, school_level) 

                if qa_array[0][0] != 0:
                    jeopardy_set.append(qa_array)
                
                time_taken = time.time() - timer_start
                if loop_count < 2 and time_taken > 10:
                    colb.write("Esto podría tardar unos pocos minutos ...")
                
                loop_count += 1

            slide_markdown += "\n|:-:|:-:|:-:|:-:|:-:|:-:|"
            for row_index in range(5):
                slide_markdown += "\n|"
                for column_index in range(6):
                    slide_markdown += f"[${(row_index+1)*200*multiplier}](#/{column_index*5 + row_index + intro_offset})|"
            slide_markdown += "\n"
			
            if len(jeopardy_set) == 6:
                answerfiletxt = ""
                for column in range(6):
                    for row in range(5):
                        slide_markdown += "\n---\n"
                        slide_markdown += f"### ({categories[column].upper()}) \n# [${((row+1)*200*multiplier)}](#/{column*5 + row + intro_offset}/1)"
                        slide_markdown += "\n--\n"
                        slide_markdown += f'<!-- .slide: data-autoslide="{question_timer*1000}" -->\n### [{jeopardy_set[column][row][0]}](#/{column*5 + row + intro_offset}/2)\nAnswer:{jeopardy_set[column][row][1]}'
                        slide_markdown += "\n--\n"
                        slide_markdown += f"### [{jeopardy_set[column][row][1]}](#/{intro_offset - 1})"
                        answerfiletxt += f"{categories[column].upper()}\n\t[{((row+1)*200*multiplier)}]: P:{jeopardy_set[column][row][0]}\n\t\tR:{jeopardy_set[column][row][1]}\n\n"
                ##slide_markdown += "<H2 align=left>TEAM 1: $5000</H2> <H2 align=right>TEAM 2: $2000</H2>" + "\n"
                slide_markdown += slide_markdown_close
                ##print ("Slide markdown\n")
                ##print (slide_markdown)

                new_key = str(uuid.uuid4())
                st.session_state.reveal = new_key
                st.session_state.markdown = slide_markdown
                st.session_state.lastdelta = st.session_state.delta
                st.session_state.delta = st.session_state.tokens - token_count_at_start 
                st.session_state.answerfiletxt = answerfiletxt

## Presenting generated content and data ======================================================
reveal_snippets = [[{ 
                        "name": '--', 
                        "code": '\n---\n## New Horizontal Slide\n' 
                    },
                    { 
                        "name": 'new slide (horizontal)', 
                        "code": '\n---\n## New Horizontal Slide\n' 
                    },
                    { 
                        "name": '-', 
                        "code": '\n--\n## New Vertical Slide\n' 
                    },
                    { 
                        "name": 'new slide (vertical)', 
                        "code": '--\n## New Vertical Slide\n' 
                    }, 
                    { 
                        "name": '<!-- .s', 
                        "code": '<!-- .slide:  -->'
                    },
                    { 
                        "name": '<!-- .e', 
                        "code": '<!-- .element: class="fragment" class="fragment" -->'
                    },
                    {
                        "name": 'slide attributes', 
                        "code": '<!-- .slide:  -->'
                    }, 
                    { 
                        "name": 'element attributes', 
                        "code": '<!-- .element: class="fragment" class="fragment" -->'
                    } 
                  ],""]

if 'css' not in st.session_state:
    st.session_state.css = """
body.reveal-viewport {
    background: #2b09cf;             /*slide background color*/
}
.reveal table {
    background: #1f069d;             /*Jeopardy board background color*/
}
.reveal table thead {                /*top|category row*/
    border: 14px solid #000000;  
}
.reveal table tr {                   /*all rows below top*/
    border: 11px solid #000000; 
}
.reveal table th, .reveal table td { /*every element of table*/
    width: 11rem;
    height: 9.5rem;
    border: 11px solid #000000;
}
.reveal table th {                   /*category element of table*/
    color: white;
    font-weight: bold;
    font-size: 0.6em;
    height: 10rem;
    text-shadow: 4px 4px #000000;
}
.reveal table td {                   /*non-category elements of table*/
    color: #ffc69675;
    font-weight: bold;
    font-size: 1.65em;
}
.reveal table td a {                 /*links in table*/
    text-shadow: 4px 4px #000000;
}
.reveal section > h1 a {             /*header 1 links outside table*/
    font-size: 2.5em; 
}
.reveal section > h2 a {             /*header 2 links outside table*/
    font-size: 1.75em;
}
.reveal section > h3 a {             /*header 3 links outside table*/
    font-size: 1.55em;
}

.reveal table td a.clicked {         /*links in table after clicked*/
    pointer-events: none; 
    cursor: default;
    color: #ffc69675;
    text-shadow: none;
}
"""

if st.session_state.markdown != "":  
    reveal_state = rs.slides(st.session_state.markdown, 
        height=410,
        config={
            "width": 1800, 
            "height": 1000, 
            "minScale": 0.1,
            "center": True, 
            "maxScale": 4, 
            "margin": 0.09,
            "controls": False,
            "history": True,
            "plugins": ["markdown", "highlight", "katex", "notes", "search", "zoom"]
            }, 
        theme="night",
        css=st.session_state.css,
        allow_unsafe_html=True,
        key=st.session_state.reveal
        )
		  
st.subheader(":computer: Developed by :orange[_Bruno and Luis_] at :blue[Zona de Inventores]")
st.caption(':sunglasses: adapted from work Chat GeoParT developed by _bouzidanas_')
