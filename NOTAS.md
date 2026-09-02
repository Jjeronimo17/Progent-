## graph.py

### Linea 9 : import io

Que hace: Controlar operaciones de entrada y salida, en nuestro caso sirve para obtener los PDF como un archivo sin necesidad de que esten
propiamente en el disco
Porque esta aqui: Porque Progent recibe el CV del usuario en un PDF, es necesario para poder procesar el PDF sin necesidad de tenerlo descargado


### Linea 10 : import json

que hace: Permite crear diccionarios de Python en base a datos que esten en formato json
Porque esta aqui: Porque el agente extrae el texto en formato JSON, despues lo convertiremos todo en un diccionario utilizando una
funcion de esta libreria


### linea 11 : import os

que hace : Permite que mi codigo interactue directamente con mi sistema operativo
Porque esta aqui: Porque lo necesitamos para poder cargar nuestras variables de entorno y consultarlas


### Linea 12 : from typing import Any, TypedDict
que hace: importa Any y TypedDict de la libreria estandar typing de python, Any permite que una variable sea cualquier cosa y
le indica a la persona que lee el codigo que asi lo es, tambien se aplica a funciones y se usa para indicar que la funcion devuelve
cualquier tipo de dato. TypedDict añade restricciones de sintaxis en los diccionarios obligandote a declarar que llaves existen
y que tipo son, es una manera de documentar.
Esto son solo comentarios al editor, no afecta a python en tiempo de ejecucion.
Porque esta aqui: Supongo que es porque los JSON tienen datos de todo tipo.

### Linea 14 : import anthropic
que hace: Supongo que es la que permite importar la consola de Anthropic para poder usar sus modelos
que hace aqui: Lo necesitamos porque nuestro agente utiliza modelos de Anthropic


### Linea 15 : from dotenv import load_dotenv
que hace: Permite cargar variables de entorno desde un archivo .env
Porque esta aqui: lo usamos para cargar nuestra API key


### Linea 16: from langgraph.graph import END, StateGraph
que hace:  es el Frame work de langGraph
Porque esta aqui: Porque es la base de nuestra arquitectura agentica.
import END, Stategraph y no solo langgraph porque son las unicas dos cosas que vamos a usar de momento,
si importamos toda la libreria tendriamos que hacer langgraph.graph.StateGraph, es mas largo de escribir


### Linea 17: from pypdf import PdfReader
que hace: Libreria que permite trabajar con PDFS
porque esta aqui: Porque Progent permite cargar CV'S en formato PDF y en el primer sprint es la manera natural de subir CV'S

### Linea 18: from prompts import SYSTEM_EXTRACCION, USER_EXTRACCION

que hace: Es mi archivo de prompts donde almacenamos todos los prompts que usara el agente SYSTEM_EXTRACCION Y USER_EXTRACCION
son prompts especificos
porque esta aqui: El agente necesita saber que hacer y los prompts son la manera de hacerselo saber


### Linea 21: load_dotenv()
que hace: Cargar las variables de entorno del archivo .env, la funcion busca sola un archivo con .env, si existieran varios en la carpeta
se tendria que pasar como argumento el nombre del archivo que si queremos usar
porque esta aqui: Lo necesitamos para cargar la API KEY y el modelo que usara el agente


### Linea 22: MODELO = os.getenv("MODELO", "claude-opus-5")
que hace: Carga el modelo que esta en el .env a python y lo guarda en la variable MODELO, si no existiera en el .env cargaria
como modelo por defecto opus-5
porque esta aqui: Lo necesitamos para poder procesar los CV'S, extraer la informacion y en general todo lo relacionado con el agente
? no entiendo: Antes pensaba que os no se usaba para nada, pero veo que se usa aca, no entiendo porque lo usamos para en este caso
cargar un archivo

### Linea 23: cliente = anthropic.Anthropic()
que hace: Cargamos nuestra API key y la guardamos en la variable cliente
porque esta aqui: Lo necesitamos porque sin la API key no tenemos proveedor de modelos de inteligencia artificial y por ende el agente
no va a funcionar

### Linea 27: class EstadoPerfil(TypedDict, total=False):
que hace: Definimos la clase del estado del perfil, el estado es lo que llega a cada nodo del grafo
porque esta aqui: Porque estamos trabajando con LangGraph que en esencia es un grafo de nodos que reciben un estado, aca estamos haciendo
justo eso, definir nuestro estado. Por defecto un TypedDict exige que esten todas las llaves, total = false elimina esta restriccion


### Linea 30: pdf_bytes: bytes
que hace: Creamos la variable pdf_bytes, :bytes es la manera de indicar que estamos guardando datos de tipo bytes en esa variable
porque esta aqui: Porque un PDF es en esencia un archivo binario, bytes es el tipo de dato para datos binarios crudos. Cuando llega el PDF
en realidad llega es una serie de bytes

### linea 31: texto : str
que hace: Crear variable texto, :str es la manera de indicar que estamos guardando datos de tipo string en esa variable
porque esta aqui: es donde almacenaremos todo el texto extraido del PDF y sin formato alguno, solo texto

### Linea 32: perfil :dict[str, Any]
que hace: creamos un diccionario llamado perfil, :dict[str, Any] nos dice que el nombre de las llaves es de tipo string y que los datos son cualquier tipo
porque esta aqui: Es donde guardaremos toda la informacion del perfil, como puede haber informacion de todos los tipos por eso ponemos Any


### Linea 33: errores :list[str]
que hace: creamos una lista llamada errores, :list[str] nos indica que los datos de la lista seran de tipo string
porque esta aqui:esto nos permite saber que errores entraron a cada nodo y que errores
salieron de cada nodo, estos errores se los podemos comunicar mas adelante al usuario si es necesario

### Linea 39: def leer_pdf(estado: EstadoPerfil) -> EstadoPerfil
que hace: definimos nuestro primer nodo que sera donde saquemos el texto del PDF, recibe un estado de tipo EstadoPerfil y devuelve
un EstadoPerfil
porque esta aqui: Para extraer todo el texto del PDF y posterior a esto interpretarlo

### Linea 40: lector = PdfReader(io.BytesIO(estado["pdf_bytes"]))
que hace: La parte mas interna recibe los bytes del PDF que contiene el CV, io.BytesIo, se encarga se envolver esos bytes en un objeto
que se comporta como un archivo abierto, es necesario porque PdfReader necesitaria normalmente la ruta del archivo, pero como el archivo
no esta descargado en disco lo hacemos de esta manera. Por ultimo PdfReader es el que se encarga de transformar esos bytes crudos en un
documento
porque esta aqui: Porque necesitamos que Python pueda ver la informacion del PDF, pero al cargarlo python solo recibe los bytes crudos
del pdf, no la informacion como tal. Es como reconstruir el PDF para que python lo pueda ver

### Linea 41: paginas = [(p.extract_text() or "") for p in lector.pages]
que hace: Extraer el texto de cada pagina del PDf que fue construida en lector con PdfReader
porque esta aqui: lo necesitamos para poder sacar el texto de cada pagina

### Linea 42: texto = "\n".join(paginas).strip()
que hace: Une el texto de cada pagina añadiendo un salto de linea entre cada pagina, strip() se encarga de eliminar los espacios o saltos
de linea que existan AL INICIO Y AL FINAL del texto, sirve para tener el texto lo mas claro posible eliminando espacios innecesarios
Porque esta aqui: Evitamos mediciones engañosas, si quisieramos saber la longitud del texto, si tenemos espacios en blanco nos daria
una longitud mucho mayor a la real

### Linea 44: errores = list(estado.get("errores", []))
que hace: Crea una copia de la lista presente en el diccionario de estados. "errores" es el nombre de la llave presente en el diccionario
original, "[]". Es lo que pasaria si no encontrara esa llave, en nuestro caso siempre la va a encontrar porque cuando se llama a el grafo
se le pasa la variable desde el inicio lo que inicializa la llave con una lista vacia por defecto. Pero es seguridad por si en algun momento
se cambia la forma en la que se llama el grafo.
### Linea 45:  if len(texto) < 50:
que hace: Es la condicion para saber si vamos a catalogar el escaneo con un error o no. Utilizamos len < 50 porque en la practica
ningun CV real tiene una longitud tan pequeña
porque esta aqui: Si no existiera aceptariamos absolutamente todo incluyendo textos vacios, la condicion tampoco puede ser len < 1
ya que aceptariamos CV'S incompletos o con muy poca informacio, y en la practica incluso aunque el PDF este vacio no tiene len < 1

### Linea 46:  errores.append( ... )
que hace: si se cumple la condicion metemos el mensaje de error al final de la lista, .append es lo que hace esto, es el equivalente a
push_back en c++
porque esta aqui: Porque si la longitud del texto es menor a 50 probablemente el CV sea incorrecto y por ende es un error, el append empuja
ese mensaje de error que nosotros establecemos al final de la lista

### Linea 50: return {"texto": texto, "errores": errores}
que hace: Retornamos un diccionario con dos llaves, una "texto" y otra "errores" y les asignamos como valor nuestro texto completo y nuestra
lista de errores
porque esta aqui: Porque cada nodo devuelve lo que modifico del estado original SIN CAMBIARLO, el estado original nunca se cambia

### Linea 56: def extraer(estado: EstadoPerfil) -> EstadoPerfil:
que hace: Definimos la funcion que se va a encargar de EXTRAER la informacion del texto que sacamos en leer, recibe un estado
de tipo EstadoPerfil y devuelve alo de ese mismo tipo(EstadoPerfil)
Porque esta aqui: Porque en la anterior funcion lo unico que hicimos fue extraer todo el texto del PDF, pero no lo procesamos. En esta
funcion es donde vamos a sacar la INFORMACION del texto

### Linea 57: if estado.get("errores"):
que hace: Busca la etiqueta de "errores" en estado y mira la lista, si la lista no esta vacia entra en la condicion
porque esta aqui: Si hay un error, no sigue el proceso

### Linea 58: return {}
que hace: Si se entro a la condicion del if simplemente corta y devuelve un diccionario vacio (Tiene sentido porque no proceso nada)
porque esta aqui: Porque si hay un error no nos conviene seguir, ya sabemos que si algo fallo las siguientes fases probablemente se alteren
o no sean correctas. Es mejor cortar y evitar procesamientos innecesarios

### Linea 60: respuesta = cliente.messages.create(...)
que hace: Es la manera que tenemos de mandarle un texto estructurado a Anthropic (Proveedor de IA) y que este nos devuelva una respuesta
Procesada por el modelo, cliente es Anthropic

### Linea 61: model=MODELO,
que hace: especificamos el modelo que usara Anthropic, en nuestro caso opus-5
porque esta aqui: Tenemos que decir que modelo queremos que haga el procesamiento

### Linea 62: max_tokens=4000
que hace: Es la cantidad MAXIMA de tokens que el modelo puede generar en su respuesta, no es una obligacion, si la respuesta completa
solo requiere 2000 tokens, eso gasta. El numero es preventivo, asi como pusimos 4000 podemos poner 10000
porque esta aqui: Anthropic exige ponerlo, es importante tampoco poner un numero muy bajo porque las respuestas se cortarian y generaria errores

### Linea 63: system=SYSTEM_EXTRACCION
que hace: system es el prompt que define y condiciona al modelo: que rol tendra, como va a responder, que reglas sigue. En nuestro caso ese prompt esta descrito en nuestro archivo de prompts y lo especifica SYSTEM_EXTRACCION

### Linea 64:  messages=[ ... ]
que hace: Es la forma en la que la API espera que llegue el mensaje
porque esta aqui: Es necesario porque tenemos que indicarle a la API como le van a llegar los mensajes, Anthropic lo exige

### Linea 65:{"role": "user", "content": USER_EXTRACCION.format(texto=estado["texto"])}
que hace: "role" y "content" son llaves de un diccionario externo, role es quien manda el mensaje. Existe "user" y "assistant", user es el usuario y assistant es el modelo. En este caso el mensaje lo envia el usuario, el contenido viene de USER_EXTRACCION que esta descrito en nuestro archivo de prompts, .format porque USER_EXTRACCION tiene un hueco {texto}, ahi es donde se espera que se ponga el analisis del CV,
format es en el encargado de rellenar ese hueco entre llaves automaticamente, utilizando el texto presente en el estado
porque esta aqui: Esta es la estructura completa de como la API recibe el mensaje, la API no recuerda nada, asi que si quisieramos usar las respuestas que esta dio deberiamos hacer lo mismo pero marcando el "role": "assistant"

### Linea 69:  bloques = [b.text for b in respuesta.content if b.type == "text"]
que hace: Toma el texto de cada bloque b en la respuesta del modelo, pero solo de los bloques que tengan de tipo "text" , .content en este contexto es un atributo del objeto que permite obtener la respuesta del modelo en bloques, por eso hay que recorrerla
porque esta aqui: Porque en este apartado es donde comenzamos a estructurar la respuesta del modelo.

### Linea 70: errores = list(estado.get("errores", []))
que hace: Crea una copia de la lista presente en el diccionario de estados. "errores" es el nombre de la llave presente en el diccionario
original, "[]". Es lo que pasaria si no encontrara esa llave, en nuestro caso siempre la va a encontrar porque cuando se llama a el grafo
se le pasa la variable desde el inicio lo que inicializa la llave con una lista vacia por defecto. Pero es seguridad por si en algun momento
se cambia la forma en la que se llama el grafo.

### Linea 71: if not bloques:
que hace: si bloques no tiene contenido entra al if, en este caso si bloques no tiene contenido hay un error, por eso dentro del if nos encargaremos de señalar ese error y hace return
porque esta aqui: En bloques debe estar la respuesta del modelo, si no hay respuesta del modelo algo salio mal y no se puede continuar

### Linea 72: errores.append("El modelo no devolvio texto.")
que hace: empujamos al final de la lista de errores el error que sucedio en este caso, si bloques es vacio el modelo no dio respuesta asi que eso es lo que reportamos
porque esta aqui: Porque una vez encontramos un error debemos meterlo a la lista, siempre hacemos una copia porque nunca modificamos la lista original de errores, cada nodo reporta los errores que encuentra

### Linea 73: return {"errores": errores}
que hace: Retornamos cortando la funcion y devolviendo un diccionario con la llave "Errores" y de contenido el presente en la lista que copiamos anteriormente
porque esta aqui: necesitamos hacer return porque si no el codigo si señalaria el error pero seguiria ejecutandose y ese no es el comportamiento que deberia tener

### Linea 74: crudo = "\n".join(bloques).strip()
que hace: Juntamos toda la respuesta del modelo en un texto solo, eliminando los espacios del inicio y del final
porque esta aqui: Actualmente tenemos la respuesta del modelo separada en bloques, necesitamso unirlos y eliminar los espacios al inicio y al final para poder procesar mejor la respuesta del modelo y despues formatear mejor el archivo

### Linea 76: if crudo.startswith("```"):
que hace: Es una guarda por si el modelo envuelve el JSON en un bloque de codigo MD, en formato MD crudo comenzaria con esas comillas y entraria al if
porque esta aqui: porque si lo entrega en MD cuando hagamos json.loads este fallaria, necesitamos asegurarnos de que siempre estemos en formato JSON

### linea 77: crudo = crudo.split("```")[1]
que hace: Partimos crudo cada vez que encuentre esas comillas, en este caso tendriamos algo asi: "``` json ........ ```" El primer corte nos dejaria ["", "json ........ ```"] y el segundo corte nos dejaria: ["", json ........, ""]
el indice uno es para coger justamente la parte del centro que es la informacion real que nos conviene
porque esta aqui: Esto es lo que nos permite saltarnos la envoltura del formato MD, recordemos que todo lo trabajamos siempre en JSON

### Linea 78: if crudo.startswith("json"):
que hace: Ahora revisamos si crudo comienza con json, si lo hace entramos al if.
porque esta aqui: El motivo de esto es que la etiqueta de json no nos sirve, un formato real de JSON empieza con {} y en este caso empieza con una palabra

### Linea 79: crudo = crudo[4:]
que hace: Crudo comienza apartir del 4 caracter, que en este caso seria justo despues de terminar la palabra json
porque esta aqui: Porque de esta manera saltamos la etiqueta innecesaria y nos queda en el formato que buscamos

### Linea 80: crudo = crudo.strip()
que hace: Nos aseguramos de eliminar espacios al inicio y final de crudo
porque esta aqui: Para evitarnos problema de longitudes

### Linea 82: inicio, fin = crudo.find("{"), crudo.rfind("}")
que hace: creamos dos varibles (inicio y fin). Inicio la inicializamos con la primer aparacion de { en la respuesta cruda, y fin lo inicializamos con la ultima aparicion de } en la respuesta cruda
porque esta aqui: Son nuestros limitadores de la respuesta, de esta manera tenemos el indice en el que inicio la respuesta y el indice en el que termina la respuesta

### Linea 83: if inicio != -1 and fin != -1:
que hace:
