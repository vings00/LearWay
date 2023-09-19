import base64
from pyvis.network import Network
from clarifai_grpc.channel.clarifai_channel import ClarifaiChannel
from clarifai_grpc.grpc.api import resources_pb2, service_pb2, service_pb2_grpc
from clarifai_grpc.grpc.api.status import status_code_pb2
import streamlit as st
import webbrowser

PAT = st.secrets.PAT
USER_ID = 'meta'
APP_ID = 'Llama-2'
MODEL_ID = 'llama2-7b-chat'
MODEL_VERSION_ID = 'e52af5d6bc22445aa7a6761f327f7129'
PROMPT_TEMPL = '<s>[INST]<<SYS>> You are a helpful, respectful and honest assistant. Always answer as helpfully as possible. You will split the main topic in some main subtopics.; Always answer using the template i will give you now: [Main Topic]: # [Subtopic] # [Subtopic] # [Subtopic] # [Subtopic] #END Create a list of main subtopics only using this template. YOU MUST ALWAYS END THE LIST OF TOPICS WITH #END. Exapmle of your output: [Main Topic]: Linear Algebra: #Vector Spaces #Linear Transformations #Matrices #Linear Equations #Determinants #Eigenvalues and Eigenvectors #END YOU MUST ALWAYS END THE LIST OF TOPICS WITH #END You must make the list with exact same stucture as in the template. If a question does not make any sense, or is not factually coherent, explain why instead of answering something not correct. If you dont know the answer to a question, please dont share false information. YOU MUST ALWAYS END THE LIST OF TOPICS WITH #END. CREATE MAX 12 SUBTOPICS <</SYS>> Give me a list of subtopics for the subject Linear Algebra [/INST] [Main Topic]: Linear Algebra: #Vector Spaces #Linear Transformations #Matrices #Linear Equations #Determinants #Eigenvalues and Eigenvectors #Orthogonal Diagonalization #Singular Value Decomposition (SVD) #Eigenvalue Decomposition #END [INST] Give me a list of subtopics for the subject Neurobiology [/INST] [Main Topic]: Neurobiology #Neuron Structure and Function #Neuroanatomy #Neural Development #Neurotransmitters and Neuromodulators #Neuroplasticity #Sensory Systems #Motor Systems #Learning and Memory #Neurological Disorders #Neurobiology and Behavior #Neurogenetics and Epigenetics #Neuroethics and Neurophilosophy #END [INST] Give me a list of subtopics for the subject '
PROMPT_TEMPL_SUBTOP = '<s>[INST]<<SYS>> You are a helpful, respectful and honest assistant. Always answer as helpfully as possible. You must split the topic in some subtopics. Always answer using the template i will give you now: # [Subtopic] # [Subtopic] # [Subtopic] # [Subtopic] #END Create a list of subtopics only using this template. YOU MUST ALWAYS END THE LIST OF TOPICS WITH #END Exapmle of your output for the topic Vector Spaces in Linear Algebra: #Definition and examples of vector spaces\n #Linear independence and dependence #Basis and dimension #Subspaces #END YOU MUST ALWAYS END THE LIST OF TOPICS WITH #END You must make the list with exact same stucture as in the template. If a question does not make any sense, or is not factually coherent, explain why instead of answering something not correct. If you dont know the answer to a question, please dont share false information. YOU MUST ALWAYS END THE LIST OF TOPICS WITH #END TRY NOT CREATE TOO MANY SUBTOPICS <</SYS>> Give me a list of subtopics for the subject Neuroanatomy in Neurobiology [/INST] #Central nervous system (CNS) and peripheral nervous system (PNS) #Brain regions and their functions #Spinal cord structure and function #END [INST] Give me a list of subtopics for the subject Data Structures in Python [/INST] #Lists #Tuples #Dictionaries #Sets #Stacks #Queues #Linked Lists #Trees #Graphs #Hashing #Heaps #END [INST] Give me a list of subtopics for the subject '
def generate(text: str) -> str:
    channel = ClarifaiChannel.get_grpc_channel()
    stub = service_pb2_grpc.V2Stub(channel)

    metadata = (('authorization', 'Key ' + PAT),)

    userDataObject = resources_pb2.UserAppIDSet(user_id=USER_ID, app_id=APP_ID)

    post_model_outputs_response = stub.PostModelOutputs(
        service_pb2.PostModelOutputsRequest(
            user_app_id=userDataObject,

            model_id=MODEL_ID,
            version_id=MODEL_VERSION_ID,
            inputs=[
                resources_pb2.Input(
                    data=resources_pb2.Data(
                        text=resources_pb2.Text(
                            raw=text
                        )
                    )
                )
            ]
        ),
        metadata=metadata
    )
    if post_model_outputs_response.status.code != status_code_pb2.SUCCESS:
        print(post_model_outputs_response.status)
        raise Exception(f"Post model outputs failed, status: {post_model_outputs_response.status.description}")

    output = post_model_outputs_response.outputs[0]
    text_output = str(output.data.text.raw)
    return text_output

class RoadMap:
    def __init__(self):
        self.__network = Network(height="800px", directed=True, neighborhood_highlight=True, select_menu=True,)
        pass

    def get_title(self, name):
        for char in name:
            if not char.isalpha() or not char.isascii() or not char.islower():
                self.__name = "RoadMap"
                return
        self.__name = name

    def fit_text(self, text: str):
        print(text)
        idx = text.find("]: ") + 3

        mainTop = ""

        while text[idx] != '#':
            mainTop += text[idx]
            idx += 1
        mainTop = mainTop.rstrip()

        self.__name = mainTop

        idx += 1

        newIdx = text.find("END")
        strSubtopics = text[idx:newIdx]

        subtopics = strSubtopics.split('#')
        subtopics = subtopics[0:len(subtopics) - 1]
        self.__subtopics = subtopics

    def __fill_graph(self):
        self.__network.add_node(self.__name,
                                title=self.__name,
                                shape="box",
                                label=self.__name,
                                color="#E8E048")
        self.__network.add_nodes(self.__subtopics,
                                 title=self.__subtopics,
                                 shape=["box"] * len(self.__subtopics),
                                 label=self.__subtopics,
                                 color=['#FFE65D'] * len(self.__subtopics))

        self.__network.add_edge(self.__name, self.__subtopics[0], width=5, length=400)

        for i in range(len(self.__subtopics) - 1):
            self.__network.add_edge(self.__subtopics[i], self.__subtopics[i+1], width=5, length=400)

        self.__fill_subtopics()

    def __fill_subtopics(self):
        used = set()

        for sub in self.__subtopics:
            newRaw = PROMPT_TEMPL_SUBTOP + sub + ' [/INST]'
            text = generate(newRaw)

            idxStart = text.find("#")
            idxEnd = text.find("END")
            text = text[idxStart + 1:idxEnd]

            deepSubtopics = text.split('#')
            deepSubtopics = deepSubtopics[0:len(deepSubtopics) - 1]

            filtered_deepSubtopics = []
            for subtopic in deepSubtopics:
                if len(subtopic) <= 40:
                    filtered_deepSubtopics.append(subtopic)
            deepSubtopics = filtered_deepSubtopics

            newDeep, used = self.__check_old_words(used, deepSubtopics)
            deepSubtopics = list(newDeep)

            deepSubtopics = self.__check_length(deepSubtopics)

            self.__network.add_nodes(deepSubtopics,
                                     title=deepSubtopics,
                                     shape=["box"] * len(deepSubtopics),
                                     label=deepSubtopics,
                                     color=['#E0FF4F'] * len(deepSubtopics))

            for deep in deepSubtopics:
                self.__network.add_edge(sub, deep, width=2, length=200)

    def __check_old_words(self, used, subtopics):
        newSet = set(subtopics)

        newSet.difference_update(used)
        used.update(newSet)

        return newSet, used

    def __check_length(self, subtopics):
        newTopics = list()

        for sub in subtopics:
            flag = False
            for ch in sub:
                if ch.isalpha():
                    flag = True

            if flag:
                newTopics.append(sub)

        return newTopics

    def show(self):
        self.__fill_graph()
        self.__network.widget = True

        #webbrowser.open_new_tab(self.__network.generate_html(name=theme+'.html', notebook=False))
        html_content = self.__network.generate_html(name=theme + '.html', notebook=False)
        with open(theme + '.html', 'w') as f:
            f.write(html_content)

        # Откройте файл в отдельном окне браузера
        webbrowser.open_new_tab(theme + '.html')


with open("ROADMAP.gif", "rb") as file_:
    contents = file_.read()

data_url = base64.b64encode(contents).decode("utf-8")

st.markdown(
    f"""
    <style>
    .centered-title {{
        text-align: center;
    }}
    .centered-title2 {{
        text-align: center;
        font-size: 5em;
    }}
    </style>
    <div class="centered-title">
        <h2>LearnWay</h2>
    </div>
    <div class="centered-title2">
        <h1 style="font-size:5.5vw">Build your</h1>
    </div>
    """,
    unsafe_allow_html=True
)

st.markdown(
    f"""
    <style>
    .centered-image {{
        display: flex;
        justify-content: center;
        align-items: flex-start;
        height: auto;
        padding-top: 10vh;
        padding-bottom: 20vh;
    }}
    .resized-image {{
        max-width: 120%;
    }}
    </style>
    <div class="centered-image">
        <img class="resized-image" src="data:image/gif;base64,{data_url}" alt="Изображение">
    </div>
    """,
    unsafe_allow_html=True
)

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown(
        f"""
        <style>
        .how_to_use {{
            display: flex;
            justify-content: center;
            height: auto;
            padding-top: 50px;
        }}
        </style>
        <div class="how_to_use">
            <h1 style="font-size: 5.5vw">HOW TO USE</h1>
        </div>
        """,
        unsafe_allow_html=True)

with col3:
    st.markdown(
        f"""
        <style>
        .how_to_use {{
            display: flex;
            justify-content: flex-start;
            height: auto;
            padding-top: 50px;
        }}
        </style>
        <div class="how_to_use">
            <h2 style="font-size: 2.3vw">1. Choose a topic to explore<br /><br />
            2. Enter the topic to the textbox below<br /><br />
            3. Enjoy!</h2>
        </div>
        """,
        unsafe_allow_html=True)

st.markdown(
    f"""
    <style>
    .text-box {{
        display: flex;
        justify-content: center;
        height: auto;
        padding-top: 20vh;
    }}
    </style>
    <div class="text-box">
        <h1 style="font-size: 2vw">  Enter your topic here 👇</h2>
    </div>
    """,
    unsafe_allow_html=True)

theme = st.text_input("", "")

def check(text: str):
    prompt = "<s><<SYS>> Answer me YES or NO if the word i will write is sutable for creating a roadmap. It can be a part of science such as Math, Computer Science or other Subject, please write only 1 word - Yes or No <</SYS>> [INST] Is LDKAD suitable for creating a list of subtopics? [/INST] No [INST] Is Algebra suitable for creating a list of subtopics? [/INST] Yes [INST] Is Marketing suitable for creating a list of subtopics? [/INST] Yes [INST] Is Skin Cancer suitable for creating a list of subtopics? [/INST] Yes [INST] Is Management suitable for creating a list of subtopics? [/INST] Yes [INST] Is kkksf suitable for creating a list of subtopics? [/INST] No [INST] Is Lama suitable for creating a list of subtopics?[/INST] No [INST] Is C++ suitable for creating a list of subtopics?[/INST] Yes [INST] Is History of Russia suitable for creating a list of subtopics?[/INST] Yes [INST] Is Biology suitable for creating a list of subtopics?[/INST] Yes [INST] Is JavaScript suitable for creating a list of subtopics? [/INST] Yes [INST] Is "
    prompt += text + " suitable for creating a list of subtopics? [/INST]"

    answer = generate(prompt)

    if answer.find("Yes") > 0 and answer.find("Yes") < 5:
        return True

    return False

col1, col2, col3 = st.columns(3)


with col2:
    if st.button("GENERATE ROADMAP🧠", key="generate_button"):
        with st.spinner("Loading, please wait."):
            if check(theme):
                RAW_TEXT = PROMPT_TEMPL + theme + ' [/INST]'
                rd = RoadMap()
                rd.get_title(theme)
                rd.fit_text(generate(RAW_TEXT))

                rd.show()

                st.success("Done")
            else:
                st.warning("Please, enter your theme once again!")