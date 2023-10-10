import streamlit as st
import time
import tiktoken
import openai

## Functions ========================================================================
token_count_at_start = 0
def num_tokens_from_string(string: str, encoding_name="cl100k_base") -> int:
    """Returns the number of tokens in a text string."""
    encoding = tiktoken.get_encoding(encoding_name)
    num_tokens = len(encoding.encode(string))
    return num_tokens

messages=[
          {"role": "system", "content": "You are a helpful trivia game creation assistant."}
         ]
def query_ai(message_text, model="gpt-3.5-turbo", temperature=0.7):
    number_of_tokens = st.session_state.tokens + num_tokens_from_string(message_text)
    messages.append({"role": "user", "content": message_text})
    try:
        output = openai.ChatCompletion.create(
                    model=model,
                    messages=messages,
                    temperature=temperature,
                    )
    except openai.error.Timeout as e:
        #Handle timeout error, e.g. retry or log
        st.error(f"ERROR! OpenAI API tiempo de la solicitud excedido: {e}")
        pass
    except openai.error.APIError as e:
        #Handle API error, e.g. retry or log
        st.error(f"ERROR! OpenAI API respondió API Error: {e}")
        pass
    except openai.error.APIConnectionError as e:
        #Handle connection error, e.g. check network or log
        st.error(f"ERROR! OpenAI API fallo en la conexión: {e}")
        pass
    except openai.error.InvalidRequestError as e:
        #Handle invalid request error, e.g. validate parameters or log
        st.error(f"ERROR! OpenAI API solicitud inválida: {e}")
        pass
    except openai.error.AuthenticationError as e:
        #Handle authentication error, e.g. check credentials or log
        st.error(f"ERROR! OpenAI API solicitud no autorizada: {e}")
        pass
    except openai.error.PermissionError as e:
        #Handle permission error, e.g. check scope or log
        st.error(f"ERROR! OpenAI API solicitud no permitida: {e}")
        pass
    except openai.error.RateLimitError as e:
        #Handle rate limit error, e.g. wait or log
        st.error(f"ERROR! OpenAI API límite de peticiones excedido. Espere un momento y vuelva a intentar.")
        pass
    except Exception as e:
        #Handle other exceptions, e.g. log
        st.error(f"ERROR! OpenAI API solicitud fallida: {e}")
        pass

    if output.choices[0].message.content:
        st.session_state.tokens = number_of_tokens + num_tokens_from_string(output.choices[0].message.content)
        return output.choices[0].message.content
    else:
        return "Error: Sin respuesta de AI."

def get_jeopardy_trivia(category, school_year, school_level):
    response = query_ai("La categoría Jeopardy es '" + category + "' y la cantidad de pesos de esta categoría es '$200', '$400', '$600', '$800', '$1000' según su nivel de dificultad. Genera un estilo de pregunta + respuesta para cada cantidad de pesos en la categoría del grado escolar '" + school_year + "' de educación '" + school_level + "'. Proporciona una lista de cada una de las preguntas con su correspondiente respuesta con el formato '- cantidad en pesos | Pregunta : Respuesta\n'.")
    print(response+"\n")
    trivia_questions = [[0],[0],[0],[0],[0]]
    if response:
        lines = response.split("\n")
        for line in lines:
            print("Linea: " + line)
            if line.startswith("$") or line.startswith("-"):
                row = line.split("|")
                if len(row) == 2:
                    qa = row[1].replace("Pregunta:", "").replace("pregunta:", "").replace("p:", "").replace("P:", "").split(":")
                    if len(qa) == 2:
                        amount = row[0].replace("$", "").replace("-", "")
                        question = qa[0].replace("respuesta", "").replace("Respuesta", "").strip()
                        answer = qa[1].replace("respuesta", "").replace("Respuesta", "").strip()
                        if "200" in amount:
                            trivia_questions[0] = format_qa_response([question, answer])
                        elif "400" in amount:
                            trivia_questions[1] = format_qa_response([question, answer])
                        elif "600" in amount:
                            trivia_questions[2] = format_qa_response([question, answer])
                        elif "800" in amount:
                            trivia_questions[3] = format_qa_response([question, answer])
                        elif "1000" in amount:
                            trivia_questions[4] = format_qa_response([question, answer])
    ##print (trivia_questions)
    return trivia_questions

def retry_get_jeopardy_trivia(category, school_year, school_level):
    number_of_tries=2
    trivia_questions = [[0],[0],[0],[0],[0]]
    for i in range(number_of_tries):
        request_delay = 1.0
        time.sleep(request_delay)
        trivia_questions = get_jeopardy_trivia(category, school_year, school_level)
        check = True
        for array in trivia_questions:
            if len(array) < 2 or array[0] == 0:
                check = False
        if check:
            return trivia_questions
    return trivia_questions

def format_qa_response(response):
    question = response[0]
    answer = response[1]
    six_ws = ["quién", "qué", "cuándo", "dónde", "por qué", "cuál"]
    etre = ["es", "son", "fue", "fueron"]
    words_in_q = question.replace("-", "").replace(":", "").strip().split(" ")
    ans_start = ""
    if words_in_q[0].lower() in six_ws and words_in_q[1].lower() in etre:
        question = question.replace(words_in_q[0], "", 1).replace(words_in_q[1], "", 1).replace(words_in_q[2], words_in_q[2].capitalize(), 1).strip()
        ans_start = words_in_q[0].capitalize() + " " + words_in_q[1].lower() + " "
    elif words_in_q[0].lower() in six_ws:
        if words_in_q[0].lower() == "quién":
            question = question.replace(words_in_q[0], "Esta persona", 1)
            ans_start = "Quién es "
        elif words_in_q[0].lower() == "qué":
            question = question.replace(words_in_q[0], "Esto", 1)
            ans_start = "Qué es "
    words_in_a = answer.replace("-", "").replace(":", "").strip().split(" ")
    if words_in_a[0].lower() not in six_ws:
        answer = ans_start + answer.replace(words_in_a[0], words_in_a[0].lower(), 1).strip()
    if question.strip().endswith("?"):
        question = question.strip().rsplit("?", 1)[0]
    answer = answer.strip()
    if not answer.endswith("?"):
        if answer.endswith("."):
            answer = answer.rsplit(".", 1)[0]
        answer = answer.strip() + "?"

    return [question, answer.upper()]

