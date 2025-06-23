/**
 * Clase para la ejecución automática de scripts SQL sobre una base de datos Oracle.
 * 
 * El programa lee un archivo de configuración (OracleScriptRunner.ini) donde se especifican los datos
 * de conexión a la base de datos (IP, puerto, SID, usuario, clave), el archivo SQL a procesar,
 * la codificación del archivo y si se debe eliminar el punto y coma al final de cada sentencia.
 * 
 * Si se proporciona un parámetro al ejecutar la aplicación, este se usará como nombre del
 * archivo SQL en lugar del indicado en la configuración.
 * 
 * El programa procesa cada línea del archivo SQL, eliminando comentarios (líneas que empiezan
 * por "--" o bloques entre "/ *" y "* /"), y ejecuta las sentencias SQL una a una.
 * 
 * - Las sentencias ejecutadas correctamente se guardan en el archivo OK.SQL (modo append).
 * - Las sentencias con error se guardan en el archivo KO.SQL (modo append).
 * - Los comentarios se guardan también en OK.SQL.
 * 
 * Durante la ejecución, se muestra una salida gráfica:
 *   - "-" (azul) por cada comentario encontrado
 *   - "." (verde) por cada sentencia ejecutada correctamente
 *   - "x" (rojo) por cada error al ejecutar una sentencia
 * 
 * El programa permite interrumpir la ejecución pulsando ENTER.
 * 
 * El archivo SQL original se actualiza al finalizar, eliminando las 
 * sentencias ejecutadas correctamente y dejando solo las que generaron error.
 */
import java.io.*;
import java.sql.*;
import java.util.*;
import java.util.regex.*;

public class OracleScriptRunner {

    private static Map<String, String> leerConfiguracion(String ruta) throws IOException {
        Map<String, String> config = new HashMap<>();
        BufferedReader reader = new BufferedReader(new FileReader(ruta));
        String linea;
        while ((linea = reader.readLine()) != null) {
            linea = linea.trim();
            if (linea.isEmpty() || linea.startsWith("#")) continue;
            String[] partes = linea.split("=", 2);
            if (partes.length >= 2) {
                config.put(partes[0].trim(), partes[1].trim());
            }
        }
        reader.close();
        return config;
    }

    // Función para eliminar comentarios y devolver si es comentario
    private static String[] eliminarComentarios(String linea) {
        boolean esComentario = linea.trim().toUpperCase().startsWith("REM") || linea.trim().startsWith("--") || (linea.trim().startsWith("/*") && linea.trim().endsWith("*/"));

        linea = linea.replaceAll("^rem.*", "");
        linea = linea.replaceAll("^REM.*", "");
        linea = linea.replaceAll("^--.*", "");
        linea = linea.replaceAll("^/\\*.*?\\*/", "");

        return new String[] { linea.trim(), esComentario ? "COMENTARIO" : "SENTENCIA" };
    }

    // Imprimir caracteres con color (solo funciona en terminales ANSI)
    private static void printColored(String color, String text) {
        String code = "";
        switch (color) {
            case "BLUE": code = "\u001B[34m"; break;
            case "GREEN": code = "\u001B[32m"; break;
            case "RED": code = "\u001B[31m"; break;
            case "RESET": code = "\u001B[0m"; break;
        }
        System.out.print(code + text + (color.equals("RESET") ? "" : "\u001B[0m"));
    }

    public static boolean eliminarArchivoKO() {
        File archivo = new File("KO.SQL");
        if (archivo.exists()) {
            return archivo.delete();
        }
        return false;
    }

    public static void main(String[] args) {
        try {
            Map<String, String> config = leerConfiguracion("OracleScriptRunner.ini");
            String codificacion = config.getOrDefault("CODIFICACION", "UTF-8");
            String ip = config.get("IP");
            String puerto = config.get("PUERTO");
            String sid = config.get("SID");
            String usuario = config.get("USUARIO");
            String clave = config.get("CLAVE");
            String archivoSql = config.get("ARCHIVO_SQL");
            if (args.length > 0) {
                archivoSql = args[0];
            }
            String eliminarPuntoYComa = config.getOrDefault("ELIMINAR_PUNTO_Y_COMA", "SI").toUpperCase();

            String url = "jdbc:oracle:thin:@" + ip + ":" + puerto + ":" + sid;

            Connection conn;
            try {
                conn = DriverManager.getConnection(url, usuario, clave);
                conn.setAutoCommit(false);
            } catch (SQLException e) {
                System.err.println("Error de conexión: " + e.getMessage());
                return;
            }

            eliminarArchivoKO();

            List<String> lineas = new ArrayList<>();
            try (BufferedReader reader = new BufferedReader(
                    new InputStreamReader(new FileInputStream(archivoSql), codificacion))) {
                String linea;
                while ((linea = reader.readLine()) != null) {
                    lineas.add(linea);
                }
            } catch (FileNotFoundException e) {
                System.err.println("Archivo " + archivoSql + " no encontrado");
                return;
            }

            List<String> lineasRestantes = new ArrayList<>();
            final boolean[] detenerProceso = {false};

            System.out.println("Procesando sentencias. Presiona ENTER para salir...");

            Thread inputThread = new Thread(() -> {
                try {
                    System.in.read();
                    detenerProceso[0] = true;
                } catch (IOException ignored) {}
            });
            inputThread.start();

            for (String linea : lineas) {
                if (detenerProceso[0]) break;

                String[] resultado = eliminarComentarios(linea);
                String lineaProcesada = resultado[0];
                String tipo = resultado[1];

                // Guardamos la línea original para los archivos
                String lineaOriginal = linea.trim();

                if (tipo.equals("COMENTARIO")) {
                    // Guardar comentario en OK.SQL
                    try (BufferedWriter writer = new BufferedWriter(
                            new OutputStreamWriter(new FileOutputStream("OK.SQL", true), codificacion))) {
                        writer.write(lineaOriginal);
                        writer.newLine();
                    }
                    printColored("BLUE", "-");
                    continue;
                }

                // Eliminar punto y coma al final si está configurado
                if (eliminarPuntoYComa.equals("SI") && lineaProcesada.endsWith(";")) {
                    lineaProcesada = lineaProcesada.substring(0, lineaProcesada.length() - 1).trim();
                }

                if (!lineaProcesada.isEmpty()) {
                    try (Statement stmt = conn.createStatement()) {
                        stmt.execute(lineaProcesada);
                        conn.commit();
                        // Guardar sentencia correcta en OK.SQL
                        try (BufferedWriter writer = new BufferedWriter(
                                new OutputStreamWriter(new FileOutputStream("OK.SQL", true), codificacion))) {
                            writer.write(lineaOriginal);
                            writer.newLine();
                        }
                        printColored("GREEN", ".");
                    } catch (SQLException e) {
                        // Guardar sentencia errónea en KO.SQL
                        try (BufferedWriter writer = new BufferedWriter(
                                new OutputStreamWriter(new FileOutputStream("KO.SQL", true), codificacion))) {
                            writer.write(lineaOriginal);
                            writer.newLine();
                        }
                        printColored("RED", "x");
                        lineasRestantes.add(linea);
                    }
                } else {
                    // Línea vacía tras eliminar comentarios
                    try (BufferedWriter writer = new BufferedWriter(
                            new OutputStreamWriter(new FileOutputStream("OK.SQL", true), codificacion))) {
                        writer.write(lineaOriginal);
                        writer.newLine();
                    }
                    printColored("BLUE", "-");
                }
            }

            // Actualizar el fichero original con las líneas no ejecutadas correctamente
            try (BufferedWriter writer = new BufferedWriter(
                    new OutputStreamWriter(new FileOutputStream(archivoSql), codificacion))) {
                for (String linea : lineasRestantes) {
                    writer.write(linea);
                    writer.newLine();
                }
            }

            conn.close();
            System.out.println();
            System.out.println("Proceso finalizado.");

        } catch (Exception e) {
            System.err.println("Error general: " + e.getMessage());
        }
    }
}
