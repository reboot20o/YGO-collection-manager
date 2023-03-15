from pathlib import Path


def default_path():
    path = Path(__file__).parent

    relative_path = "../../assets/"
    return str((path / relative_path).resolve())



def location_retrieval():
    file_location = location_file_text()
    if file_exist(file_location):
        with open(file_location, "r") as f:
            db_path = f.read()
            f.close()
            return db_path
    else:
        path_to_db = input(
            "Enter the path to the location where you wish to store Eisen's Database (press enter to "
            "use default location): "
        )
        if len(path_to_db) != 0:
            path_to_db += r"\tickets.db"
        else:
            path_to_db = default_path() + r"\tickets.db"

        with open(file_location, "w") as f:
            f.write(path_to_db)
            f.close()

        return path_to_db
