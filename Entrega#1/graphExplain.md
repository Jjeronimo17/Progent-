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
que hace: Supongo que es la que permite importar la libreria de cliente de Anthropic que hace las peticiones a los modelos
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
porque esta aqui: Es una lista que se va acumulando y que la interfaz le muestra al usuario

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
que hace: Verifica que si encontrara un inicio y un final, la funcion find devuelve -1 si no encuentra lo que busca, por eso usamos el operador "!="
porque esta aqui: Es necesario para lo que viene, donde limitamos la extension del documento a unicamente lo que este contemplado entre las
llaves del formato JSON

### Linea 84: crudo = crudo[inicio : fin + 1]
que hace: limita la extension de crudo, [inicio : fin + 1] los dos puntos son de slice, basicamente crudo va a ir desde el inicio ( la primer llave abriendo) hasta el final(la ultima llave cerrando), el + 1 es porque el limite derecho no se toma, es decir si fuera desde inicio a fin estariamos tomando una posicion antes del fin real y no estariamos incluyendo la llave que cierra

### Linea 86: try:
que hace: try nos permite ejecutar un codigo riesoso que es probable que falle
porque esta aqui: Porque lo siguiente que vamos a hacer es convertir el texto crudo en formato JSON en un objeto en python, sin embargo si
crudo no esta en formato JSON ese load va a fallar, por eso lo hacemos con un try para que si falla no rompa el codigo

### Linea 87: perfil = json.loads(crudo)
que hace: Creamos un diccionario en base al texto crudo y lo almacenamos en la variable perfil
porque esta aqui: Porque el texto crudo son todos los datos que el

### Linea 88: except json.JSONDecodeError as e:
que hace: El except captura y maneja una exepcion, en este caso nuestra exepcion es que el texto no este en formato JSON, guardamos esa exepcion en una variable llamada e
porque esta aqui: Dado el caso que si falle el json.loads agarramos esa exepcion con nuestro except(catch) y lo siguiente es lo que pasa si agarramos la exepcion

### Linea 89: errores = list(estado.get("errores", []))
que hace: Crea una copia de la lista presente en el diccionario de estados. "errores" es el nombre de la llave presente en el diccionario
original, "[]". Es lo que pasaria si no encontrara esa llave, en nuestro caso siempre la va a encontrar porque cuando se llama a el grafo
se le pasa la variable desde el inicio lo que inicializa la llave con una lista vacia por defecto. Pero es seguridad por si en algun momento
se cambia la forma en la que se llama el grafo.

### Linea 90: errores.append(f"El modelo no devolvio JSON valido: {e}")
que hace: Empujamos al final de la lista el error que salio en este caso, el modelo no devolvio un texto con formato JSON
porque esta aqui: de esta manera guardamos el error que sucedio {e} da informacion detallada de porque fallo.

### linea 91: return {"errores": errores}
que hace: Devolvemos un diccionario con la llave "errores" que contiene la lista con el error que agregamos, en este caso el fallo del formato JSON
porque esta aqui: los nodos siempre tienen que devolver algo, en este caso devuelve el error que encontramos

### Linea 93: return {"perfil": perfil}
que hace: Si la linea del try funciono sin ningun problema nunca entramos al except
porque esta aqui: esto es lo que pasa si nunca entramos al except, si la linea del try funciona correctamente entonces saltamos directamente aca, retornamos un diccionario con la llave "perfil" y guardamos el diccionario con los datos de perfil extraidos del texto crudo

### linea 99: CLAVES = ["nombre_completo", "contacto", "experiencia", "educacion", "habilidades"]
que hace: en CLAVES almacenamos los nombres con los cuales accedemos a valores dentro de un diccionario
porque esta aqui: porque son las llaves de nuestro diccionario, cada llave contiene su valor correspondiente, nombre_completo contiene el nombre de la persona extraido del CV

### Linea 102: def validar(estado: EstadoPerfil) -> EstadoPerfil:
que hace: definimos la funcion validar que recibe un estado de tipo EstadoPerfil y devuelve un diccionario del mismo tipo
porque esta aqui: validar es la funcion que nos permite rectificar que el JSON si quedara con la forma adecuada

### Linea 103: if estado.get("errores"):
que hace: consultamos en el estado la el valor de la llave "errores" el cual es una lista, si la lista no esta vacia entramos al cuerpo del if
porque esta aqui: nuevamente porque si hay errores no debemos seguir con el proceso y simplemente cortar devolviendo un diccionario vacio

### Linea 104: return {}
que hace: aca es donde retornamos el diccionario vacio dado el caso de que la lista no este vacia
porque esta aqui: tenemos que cortar si encontramos errores en la lista contenida en la llave "errores"

### Linea 106: perfil = estado.get("perfil", {})
que hace: guardamos en perfil el diccionario de perfil, si no encontramos nada guardamos automaticamente un diccionario vacio
porque esta aqui: Es necesario porque sobre este es que vamos a hacer las verificaciones para saber si quedo en el formato adecuado

### Linea 107: faltantes = [c for c in CLAVES if c not in perfil]
que hace: Recorre CLAVES y busca las CLAVES que no esten en perfil, si no existe alguna faltantes se llena con esas, si todas estan en CLAVES y en perfil quiere decir que no falto nada y faltantes queda vacia
porque esta aqui: necesitamos saber que CLAVES o campos faltaron en la extraccion que hizo el agente del perfil, y eso es lo que guardamos en faltantes

### Linea 108: errores = list(estado.get("errores", []))
que hace: Crea una copia de la lista presente en el diccionario de estados. "errores" es el nombre de la llave presente en el diccionario
original, "[]". Es lo que pasaria si no encontrara esa llave, en nuestro caso siempre la va a encontrar porque cuando se llama a el grafo
se le pasa la variable desde el inicio lo que inicializa la llave con una lista vacia por defecto. Pero es seguridad por si en algun momento
se cambia la forma en la que se llama el grafo.

### Linea 109: if faltantes:
que hace: verifica si en faltantes efectivamente hay CLAVES FALTANTES, si NO esta vacia entra a la condicion del if
porque esta aqui: si hay claves faltantes quiere decir que la extraccion no se realizo de la mejor manera

### Linea 110: errores.append("Faltan claves en la respuesta: " + ", ".join(faltantes))
que hace: empuja el mensaje de error a la lista vacia que guardamos previamente en errores
porque esta aqui: Necesitamos indicar el error que sucedio, si faltan CLAVES la extraccion no fue del todo correcta.

### Linea 111: if not perfil.get("nombre_completo"):
que hace: verifica si la llave "nombre_completo" esta vacia en el diccionario de perfil, si lo esta entra en la condicion
porque esta aqui: si la llave esta vacia quiere decir que el agente no fue capaz de identificar el nombre en el CV

### Linea 112: errores.append("No se pudo identificar el nombre en la hoja de vida.")
que hace: empuja el error detectado en este caso: no se pudo identificar el nombre en la hoja de vida
porque esta aqui: porque si no se identifico el nombre en la hoja de vida es un claro error del que hay que llevar registro

### Linea 114: return {"errores": errores}
que hace: devuelve la lista con todos los errores que se añadieran en este nodo
porque esta aqui: todos los nodos deben devolver algo, este es solo un nodo de verificacion, si existen errores debe devolver todos los errores, si no existe ninguno devuelve una lista vacia

### Linea 120: def construir_grafo():
que hace: definimos la funcion que va a construir el grafo con todos los nodos
porque esta aqui: la arquitectura agentica en LangGraph se basa precisamente en un grafo con nodos

### Linea 121: g = StateGraph(EstadoPerfil)
que hace: le pasamos a LangGraph con la forma de estado que va a trabajar, esa forma es la que nosotros determinamos
porque esta aqui: porque LangGraph debe saber como es la forma de estado que han usado los nodos

### Linea 122 - 124: g.add_node("leer_pdf", leer_pdf), g.add_node("extraer", extraer), g.add_node("validar", validar):
que hacen: Añadimos a nuestro grafo todos los nodos que creamos previamente
porque esta aqui: Necesario completamente para el desarrollo de la arquitectura en LangGraph, el grado debe tener nodos y esos nodos son los que creamos antes

### Linea 126: g.set_entry_point("leer_pdf")
que hace: determinamos el punto donde va a iniciar el recorrido de nuestro grafo, en este caso leyendo el pdf
porque esta aqui: Tenemos que determinar donde va a iniciar el grafo, en este caso inicia en leer pdf, porque para poder cargar un CV necesitamos primero extraerlo de el PDF que lo contiene

### Linea 127 - 129: g.add_edge("leer_pdf", "extraer"), g.add_edge("extraer", "validar"), g.add_edge("validar", END):
que hace: add_edeg es lo que añade las aristas de un nodo a otro (conecta nodos), en el primero conectamos el nodo leer_pdf a extraer, despues extraer lo conectamos a validar y validar lo conectamos a END que es el fin del grafo
porque esta aqui: Describe el "Flujo" del grafo, es decir aca es donde determinamos como se conectan los nodos y que sigue despues de cada nodo

### Linea 131: return g.compile():
que hace: "Compila" el grafo, es decir, cierra la construccion del mismo
porque esta aqui: Porque si no hacemos esto, nos quedamos en la construccion del grafo, pero compile toma todo esto, valida si todo es correcto y crea un objeto

### Linea 134: grafo = construir_grafo():
que hace: llama a la funcion que crea el grafo y devuelve un objeto del grafo y lo guarda en una variable llamada grafo
porque esta aqui: porque construir_grafo devuelve un objeto y ese objeto debemos guardarlo en algun lado

### Linea 137: def procesar_cv(pdf_bytes: bytes) -> EstadoPerfil:
que hace: define una funcion procesar_cv que recibe como argumento los bytes del pdf y devuelve un EstadoPerfil
porque esta aqui: Es el punto de entrada del programa desde la interfaz

### Linea 139: return grafo.invoke({"pdf_bytes": pdf_bytes, "errores": []})
que hace: ejecuta el grafo compilado y le pasa como argumento los bytes del pdf que son almacenados en la llave del diccionario "pdf_bytes", tambien inicializa la lista de errores contemplada en la llave "errores" como vacia
porque esta aqui: Esto es lo que ejecuta propiamente el grafo compilado, pasa como argumentos los bytes del pdf que leer_pdf (el punto de entrada del grafo) va a utilizar, (el argumento de lee_pdf es un estado de EstadoPerfil) y los bytes almacenados en "pdf_bytes" lo son

### linea 142: if __name__ == "__main__":
que hace: Python le asigna a cada archivo una variable __name__ y si el archivo se ejecuta directamente esa variable es __main__
porque esta aqui: Porque app.py va a importar procesar_cv y esto lo que hace es evitar que streamlit intente leer el PDF

### Linea 143: import sys
que hace: es la libreria que da acceso a cosas del interpreste y del entorno de ejecucion
porque esta aqui: para poder leer el nombre del archivo que se escribe en la terminal

### Linea 145 - 149:
que hacen: Todas estas lineas son necesarias si vamos a correr directamente desde la terminal, si vamos a cargar el archivo desde la terminal el conjunto de estas lineas es lo que nos permite obtener los bytes del PDF
porque esta aqui: Permite correr el programa sin necesidad de montar streamlit
