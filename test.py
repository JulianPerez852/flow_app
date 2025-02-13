def func(result):
    import re
    import json
    texto_limpio = result.split("<think>")[1].split("</think>")[1]

    print(texto_limpio)

    texto_limpio = texto_limpio.split("```json")[1].split("```")[0]
    obj = json.loads(texto_limpio)
    
    return obj["datos_completos"]


text = """<think>
Bueno, tengo que ayudar al usuario a conseguir ciertos datos. Él ha empezado proporcionando algunos y me está pidiendo que, de manera gradual, le haga preguntas para obtener la información necesaria. Primero, veo que ya sabe el nombre del usuario: "Julián". Entonces, la próxima pregunta debe ser algo relacionado con el siguiente dato que needs be obtained.

El JSON inicial es {'nombre': '...', 'color_favorito': '...', 'comida_favorita': '...', 'datos_completos': false, 'next_question': 'Cual es tu nombre?'}. Al proporcionar el nombre, la próxima pregunta debe ser algo como "¿Cuál es tu color favorito?" para continuar el proceso.

También debo asegurarme de actualizar correctamente el siguiente campo, que es "next_question". Primero, cambio "Cual es tu nombre?" por "¿Cuál es tu color favorito?". Si el usuario responde, obtengo el color favorito y puedo formular la siguiente pregunta sobre su comida preferida.

Siempre debo mantener las respuestas en JSON solo con los datos obtenidos y actualizando constantemente "next_question" para guiar al usuario. Cuando se hayan obtenido todos los datos necesarios, finalmente pondría "datos_completos" como true.
</think>

```json
{
  "nombre": "Julián",
  "color_favorito": "",
  "comida_favorita": "",
  "datos_completos": false,
  "next_question": "¿Cuál es tu color favorito?"
}
```

"""

#print(func(text))

text_1 = """{
  "nombre": "Pedro",
  "color_favorito": "...",
  "comida_favorita": "...",
  "datos_completos": false,
  "next_question": "¿Cuál es tu color favorito?"
}"""

text_3 = """<think>
Bueno, tengo que ayudar al usuario a conseguir ciertos datos. Él ha empezado proporcionando algunos y me está pidiendo que, de manera gradual, le haga preguntas para obtener la información necesaria. Primero, veo que ya sabe el nombre del usuario: "Julián". Entonces, la próxima pregunta debe ser algo relacionado con el siguiente dato que needs be obtained.

El JSON inicial es {'nombre': '...', 'color_favorito': '...', 'comida_favorita': '...', 'datos_completos': false, 'next_question': 'Cual es tu nombre?'}. Al proporcionar el nombre, la próxima pregunta debe ser algo como "¿Cuál es tu color favorito?" para continuar el proceso.

También debo asegurarme de actualizar correctamente el siguiente campo, que es "next_question". Primero, cambio "Cual es tu nombre?" por "¿Cuál es tu color favorito?". Si el usuario responde, obtengo el color favorito y puedo formular la siguiente pregunta sobre su comida preferida.

Siempre debo mantener las respuestas en JSON solo con los datos obtenidos y actualizando constantemente "next_question" para guiar al usuario. Cuando se hayan obtenido todos los datos necesarios, finalmente pondría "datos_completos" como true.
</think>

{
  "nombre": "Julián",
  "color_favorito": "",
  "comida_favorita": "",
  "datos_completos": false,
  "next_question": "¿Cuál es tu color favorito?"
}

"""


def func2(result):
    import json

    obj = json.loads(result)

    context_str = str(obj) if not isinstance(obj, str) else obj

    print(context_str)

    return obj

#print(func2(text))


def func3(result):
    import json
    texto_limpio = result.split("<think>")[1].split("</think>")[1]
    try:
        clean_text = texto_limpio.split("```json")[1].split("```")[0]
        obj = json.loads(clean_text)
    except:
        obj = json.loads(texto_limpio)
    return obj


print(func3(text_3))
    