import argparse
import subprocess
import sys
from pathlib import Path


VERSION = "1.0.0"


def ejecutar_git(*args):
    try:
        resultado = subprocess.run(
            ["git", *args],
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
    except FileNotFoundError:
        raise RuntimeError(
            "Git no esta instalado o no esta disponible en el PATH."
        )

    if resultado.returncode != 0:
        return None, resultado.stderr.strip()

    return resultado.stdout.strip(), None


def comprobar_repositorio():
    salida, error = ejecutar_git(
        "rev-parse",
        "--is-inside-work-tree",
    )

    if salida != "true":
        detalles = error or "El directorio actual no es un repositorio Git."
        raise RuntimeError(
            f"No se encontro un repositorio Git.\nDetalles: {detalles}"
        )


def obtener_ultimo_tag():
    salida, _ = ejecutar_git(
        "describe",
        "--tags",
        "--abbrev=0",
    )

    return salida or None


def obtener_commits(ultimo_tag=None):
    if ultimo_tag:
        salida, error = ejecutar_git(
            "log",
            f"{ultimo_tag}..HEAD",
            "--pretty=format:%h|%s",
        )
    else:
        salida, error = ejecutar_git(
            "log",
            "--pretty=format:%h|%s",
        )

    if salida is None:
        raise RuntimeError(
            "No se pudo obtener el historial de Git.\n"
            f"Detalles: {error or 'error desconocido'}"
        )

    return salida


def clasificar_commit(mensaje):
    texto = mensaje.lower().strip()

    if any(palabra in texto for palabra in (
        "add",
        "added",
        "new",
        "feature",
        "create",
        "created",
    )):
        return "Added"

    if any(palabra in texto for palabra in (
        "fix",
        "fixed",
        "bug",
        "repair",
        "repaired",
        "resolve",
        "resolved",
    )):
        return "Fixed"

    if any(palabra in texto for palabra in (
        "remove",
        "removed",
        "delete",
        "deleted",
        "drop",
        "dropped",
    )):
        return "Removed"

    if any(palabra in texto for palabra in (
        "change",
        "changed",
        "update",
        "updated",
        "modify",
        "modified",
        "improve",
        "improved",
        "refactor",
    )):
        return "Changed"

    return "Other"


def clasificar_commits(commits):
    categorias = {
        "Added": [],
        "Fixed": [],
        "Changed": [],
        "Removed": [],
        "Other": [],
    }

    for linea in commits.splitlines():
        if "|" not in linea:
            continue

        hash_commit, mensaje = linea.split("|", 1)
        categoria = clasificar_commit(mensaje)

        categorias[categoria].append(
            f"- {mensaje} (`{hash_commit}`)"
        )

    return categorias


def generar_changelog(categorias, archivo_salida):
    contenido = "# Changelog\n\n"

    for categoria, elementos in categorias.items():
        contenido += f"## {categoria}\n\n"

        if elementos:
            contenido += "\n".join(elementos)
            contenido += "\n\n"
        else:
            contenido += "No changes.\n\n"

    try:
        archivo_salida.write_text(
            contenido,
            encoding="utf-8",
        )
    except OSError as error:
        raise RuntimeError(
            f"No se pudo escribir '{archivo_salida}'.\n"
            f"Detalles: {error}"
        )


def mostrar_resumen(categorias):
    total = sum(
        len(elementos)
        for elementos in categorias.values()
    )

    print()
    print("Resumen")
    print("-" * 30)
    print(f"Total de commits: {total}")
    print(f"Added:   {len(categorias['Added'])}")
    print(f"Fixed:   {len(categorias['Fixed'])}")
    print(f"Changed: {len(categorias['Changed'])}")
    print(f"Removed: {len(categorias['Removed'])}")
    print(f"Other:   {len(categorias['Other'])}")


def crear_parser():
    parser = argparse.ArgumentParser(
        prog="changelog",
        description=(
            "Genera automaticamente un CHANGELOG.md "
            "a partir del historial de Git."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "--output",
        "-o",
        default="CHANGELOG.md",
        help="Archivo de salida. Por defecto: CHANGELOG.md",
    )

    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Muestra informacion detallada.",
    )

    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {VERSION}",
    )

    return parser


def main():
    parser = crear_parser()
    args = parser.parse_args()

    archivo_salida = Path(args.output)

    try:
        if args.verbose:
            print("Comprobando repositorio Git...")

        comprobar_repositorio()

        if args.verbose:
            print("Repositorio Git encontrado.")

        ultimo_tag = obtener_ultimo_tag()

        if ultimo_tag:
            print(f"Ultimo tag: {ultimo_tag}")
        else:
            print("Ultimo tag: ninguno")
            print("Se utilizara todo el historial disponible.")

        if args.verbose:
            print("Obteniendo commits...")

        commits = obtener_commits(ultimo_tag)

        if not commits:
            print("No se encontraron commits.")

            categorias = {
                "Added": [],
                "Fixed": [],
                "Changed": [],
                "Removed": [],
                "Other": [],
            }
        else:
            categorias = clasificar_commits(commits)

        generar_changelog(categorias, archivo_salida)

        print()
        print(
            f"CHANGELOG generado: "
            f"{archivo_salida.resolve()}"
        )

        mostrar_resumen(categorias)

        return 0

    except RuntimeError as error:
        print()
        print("ERROR")
        print("-" * 30)
        print(error, file=sys.stderr)
        return 1

    except KeyboardInterrupt:
        print()
        print(
            "Operacion cancelada por el usuario.",
            file=sys.stderr,
        )
        return 130


if __name__ == "__main__":
    sys.exit(main())