"""
Script para importar una base de datos desde un fichero que contiene sentencias SQL línea a línea.

Para su correcto funcionamiento, es necesario configurar:
- Las propiedades de conexión a la base de datos (host, usuario, contraseña, etc.).
- El nombre del fichero de entrada que contiene el script SQL.

Este script está licenciado bajo la Licencia Pública General GNU (GPL).

Autor: Francisco José Serrano Rey

Se proporciona este software "tal cual", sin garantías de ningún tipo.
El autor no se hace responsable de ningún daño, pérdida de datos o cualquier otro inconveniente derivado del uso de este script.
"""

import os
import mysql.connector

class Import_MySQL_Data:
    def __init__(self):

        # Datos de conexión (CAMBIAR POR LOS QUE CORRESPONDA)
        self.server = "127.0.0.1"
        self.port = 3306
        self.bbdd = ""
        self.user = "root"
        self.passwd = ""

        # Fichero SQL de entrada (CAMBIAR POR EL QUE CORRESPONDA)
        self.ficheroSQL = "database.sql"

        # Fichero con los SQL que han dado error durante la importación
        self.errorFileName = self.ficheroSQL + ".log"

        self.conexionOk = False
        self.con = None
        self.statement = None
        self.query = ""
        self.queryFinal = ""

    def conectar(self):
        try:
            self.con = mysql.connector.connect(
                host=self.server,
                port=self.port,
                user=self.user,
                password=self.passwd,
                database=self.bbdd
            )
            self.statement = self.con.cursor()
            if self.con.is_connected():
                self.conexionOk = True
                print("Se conecta a la base de datos " + self.bbdd)
        except mysql.connector.Error as err:
            print("Error al conectarse a la base de datos: {}".format(err))
            exit(3)

    def leer_fichero_sql(self):
        if self.conexionOk:
            try:
                with open(self.ficheroSQL, 'r', encoding='utf-8') as file:  # Especificar la codificación
                    for line in file:
                        line = line.strip()
                        if line.startswith("--") or line.startswith("/*") or line.startswith("LOCK") or line.startswith("UNLOCK") or line == "":
                            print(line)
                        else:
                            self.queryFinal += line
                            if line.endswith(";"):
                                print(line)
                                errorEjecutando = False
                                try:
                                    self.statement.execute(self.queryFinal)
                                except mysql.connector.Error as err:
                                    print("Error al ejecutar sentencia: {}".format(err))
                                    errorEjecutando = True
                                if errorEjecutando:
                                    with open(self.errorFileName, 'a', encoding='utf-8') as errorFile:  # Especificar la codificación
                                        errorFile.write(self.queryFinal + "\n")
                                self.queryFinal = ""
            except FileNotFoundError:
                print("No se pudo encontrar el fichero " + self.ficheroSQL)
                exit(3)
            except UnicodeDecodeError as e:
                print(f"Error al leer el archivo {self.ficheroSQL}: {e}")
                exit(3)

    def cerrar_conexion(self):
        if self.conexionOk:
            try:
                self.statement.close()
                self.con.close()
                print("Conexión cerrada")
            except mysql.connector.Error as err:
                print("Error al cerrar la conexión: {}".format(err))

    def main(self):
        self.conectar()
        try:
            self.leer_fichero_sql()
        finally:
            self.cerrar_conexion()

if __name__ == "__main__":
    lee_fichero = Import_MySQL_Data()
    lee_fichero.main()
