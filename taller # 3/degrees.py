import csv
import sys

from util import Node, QueueFrontier

# Mapea nombres a un conjunto de person_ids (puede haber nombres repetidos)
names = {}

# Mapea person_id a un diccionario con name, birth, movies (conjunto de movie_ids)
people = {}

# Mapea movie_id a un diccionario con title, year, stars (conjunto de person_ids)
movies = {}


def load_data(directory):
    """
    Carga datos desde los archivos CSV dentro del directorio indicado.
    """
    # Cargar personas
    with open(f"{directory}/people.csv", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            people[row["id"]] = {
                "name": row["name"],
                "birth": row["birth"],
                "movies": set()
            }
            if row["name"].lower() not in names:
                names[row["name"].lower()] = {row["id"]}
            else:
                names[row["name"].lower()].add(row["id"])

    # Cargar películas
    with open(f"{directory}/movies.csv", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            movies[row["id"]] = {
                "title": row["title"],
                "year": row["year"],
                "stars": set()
            }

    # Cargar relación persona-película (stars)
    with open(f"{directory}/stars.csv", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                people[row["person_id"]]["movies"].add(row["movie_id"])
                movies[row["movie_id"]]["stars"].add(row["person_id"])
            except KeyError:
                # Si algún id no existe, simplemente se ignora esa fila
                pass


def main():
    if len(sys.argv) > 2:
        sys.exit("Uso: python degrees.py [directorio]")
    directory = sys.argv[1] if len(sys.argv) == 2 else "small"

    # Cargar datos desde los archivos
    print("Cargando datos...")
    load_data(directory)
    print("Datos cargados.")

    source = person_id_for_name(input("Nombre: "))
    if source is None:
        sys.exit("Persona no encontrada.")
    target = person_id_for_name(input("Nombre: "))
    if target is None:
        sys.exit("Persona no encontrada.")

    path = shortest_path(source, target)

    if path is None:
        print("No conectado.")
    else:
        degrees = len(path)
        print(f"{degrees} grados de separación.")
        path = [(None, source)] + path
        for i in range(degrees):
            person1 = people[path[i][1]]["name"]
            person2 = people[path[i + 1][1]]["name"]
            movie = movies[path[i + 1][0]]["title"]
            print(f"{i + 1}: {person1} y {person2} actuaron juntos en {movie}")


def shortest_path(source, target):
    """
    Retorna el camino más corto desde 'source' hasta 'target'.

    El camino es una lista de tuplas (movie_id, person_id), donde
    cada tupla indica que el person_id actuó en movie_id con la
    persona anterior en el camino.

    Si no existe camino posible, retorna None.
    """

    # Nodo inicial: la persona de origen, sin padre ni acción
    start = Node(state=source, parent=None, action=None)

    # Usamos QueueFrontier -> comportamiento FIFO -> esto es BFS
    frontier = QueueFrontier()
    frontier.add(start)

    # Conjunto de estados ya explorados
    explored = set()

    while True:

        # Si la frontera está vacía, no hay solución
        if frontier.empty():
            return None

        # Elegir un nodo de la frontera (el más antiguo, por ser FIFO)
        node = frontier.remove()

        # Si llegamos al objetivo, reconstruimos el camino
        if node.state == target:
            path = []
            while node.parent is not None:
                path.append((node.action, node.state))
                node = node.parent
            path.reverse()
            return path

        # Marcar el estado como explorado
        explored.add(node.state)

        # Expandir el nodo: agregar vecinos a la frontera
        for movie_id, person_id in neighbors_for_person(node.state):
            if not frontier.contains_state(person_id) and person_id not in explored:
                child = Node(state=person_id, parent=node, action=movie_id)

                # Optimización: si el vecino ya es el objetivo, retornar de inmediato
                if child.state == target:
                    path = []
                    while child.parent is not None:
                        path.append((child.action, child.state))
                        child = child.parent
                    path.reverse()
                    return path

                frontier.add(child)


def person_id_for_name(name):
    """
    Retorna el id de la persona a partir de su nombre,
    resolviendo ambigüedades si hay varias coincidencias.
    """
    person_ids = list(names.get(name.lower(), set()))
    if len(person_ids) == 0:
        return None
    elif len(person_ids) > 1:
        print(f"¿Cuál '{name}'?")
        for person_id in person_ids:
            person = people[person_id]
            name_str = f"ID: {person_id}, Nombre: {person['name']}, Nacimiento: {person['birth']}"
            print(name_str)
        try:
            person_id = input("ID Deseado: ")
            if person_id in person_ids:
                return person_id
        except ValueError:
            pass
        return None
    else:
        return person_ids[0]


def neighbors_for_person(person_id):
    """
    Retorna un conjunto de tuplas (movie_id, person_id) que corresponde
    a todas las personas que actuaron junto a la persona dada,
    en cualquier película.
    """
    movie_ids = people[person_id]["movies"]
    neighbors = set()
    for movie_id in movie_ids:
        for person_id in movies[movie_id]["stars"]:
            neighbors.add((movie_id, person_id))
    return neighbors


if __name__ == "__main__":
    main()