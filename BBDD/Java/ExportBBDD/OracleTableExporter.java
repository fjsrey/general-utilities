/**
 * OracleTableExporter
 * 
 * Exportador avanzado de datos y estructura de tablas para Oracle 11g y superiores.
 *
 * Esta aplicación permite exportar el esquema completo de una base de datos Oracle,
 * incluyendo tablas, secuencias, triggers y funciones, así como los datos contenidos
 * en las tablas en formato INSERT SQL portable.
 *
 * Características principales:
 * - Exporta el DDL de tablas, secuencias, triggers y funciones a archivos separados.
 * - Exporta los datos de cada tabla en formato INSERT SQL, con soporte especial para campos CLOB y BLOB.
 * - Para campos CLOB y BLOB, genera un archivo externo por cada valor, con contenido Base64.
 *   El nombre del archivo incluye el tipo (CLOB/BLOB), el nombre de la tabla, el campo y el número de registro.
 *   El INSERT generado contiene una referencia al archivo externo, facilitando la importación posterior.
 * - Soporta colores ANSI en la consola para mejorar la visibilidad de logs y progreso.
 * - Permite ocultar el cursor de la consola durante la ejecución para una mejor experiencia visual.
 *
 * Configuración:
 * - Los parámetros de conexión y configuración se leen desde el archivo "OracleTableExporter.properties".
 * - Permite indicar el esquema a exportar y la codificación de archivos.
 *
 * Notas:
 * - Para la importación de datos, se requiere un proceso adicional que lea los archivos externos de CLOB/BLOB
 *   y reconstruya los campos correspondientes.
 * - El formato de los archivos externos es: "[BLOB|CLOB]_NOMBRE-TABLA_NOMBRE-CAMPO_ID-REGISTRO.base64"
 */
import java.io.*;
import java.sql.*;
import java.util.Properties;

public class OracleTableExporter {

    // Colores ANSI para texto
    private static final String RESET = "\u001B[0m";
    private static final String BLACK = "\u001B[30m";
    private static final String RED = "\u001B[31m";
    private static final String GREEN = "\u001B[32m";
    private static final String YELLOW = "\u001B[33m";
    private static final String BLUE = "\u001B[34m";
    private static final String MAGENTA = "\u001B[35m";
    private static final String CYAN = "\u001B[36m";
    private static final String WHITE = "\u001B[37m";

    // Colores ANSI de fondo (opcional)
    private static final String BG_BLACK = "\u001B[40m";
    private static final String BG_RED = "\u001B[41m";
    private static final String BG_GREEN = "\u001B[42m";
    private static final String BG_YELLOW = "\u001B[43m";
    private static final String BG_BLUE = "\u001B[44m";
    private static final String BG_MAGENTA = "\u001B[45m";
    private static final String BG_CYAN = "\u001B[46m";
    private static final String BG_WHITE = "\u001B[47m";

    private static int fileNumber = 0;


    private static final String CONFIG_FILE = "OracleTableExporter.properties";

    public static void main(String[] args) {
        Properties config = loadConfig();
        if (config == null) return;

        String url = config.getProperty("jdbc.url");
        String user = config.getProperty("jdbc.user");
        String password = config.getProperty("jdbc.password");
        String schema = config.getProperty("jdbc.schema", user); // Si no hay schema, usa el usuario
        String encoding = config.getProperty("encoding", "UTF-8");

        // Crear carpeta de usuario si no existe
        File userDir = new File(schema);
        if (!userDir.exists()) {
            if (!userDir.mkdir()) {
                System.err.println(RED + "No se pudo crear la carpeta: " + schema + RESET);
                return;
            }
        }

        try (Connection conn = DriverManager.getConnection(url, user, password)) {
            hideCursor();
            DatabaseMetaData meta = conn.getMetaData();
            ResultSet tables = meta.getTables(null, schema.toUpperCase(), "%", new String[]{"TABLE"});

            System.out.println(CYAN + "Exportando TABLAS..." + RESET);

            while (tables.next()) {
                String tableName = tables.getString("TABLE_NAME");

                try {
                    // 1. Exportar DDL
                    System.out.println(YELLOW + "Procesando DDL de tabla: " + tableName + RESET);
                    exportTableDDL(conn, schema, tableName, userDir, encoding);

                    // 2. Exportar datos
                    System.out.println(YELLOW + "Procesando tabla: " + tableName + RESET);
                    //exportTableDataOracleRef(conn, schema, tableName, userDir, encoding);
                    //exportTableDataOracleBase64(conn, schema, tableName, userDir, encoding);
                    //exportTableDataBASE64(conn, schema, tableName, userDir, encoding);
                    exportTableDataBASE64File(conn, schema, tableName, userDir, encoding);
                    
                    // 3. Actualizamos el % de exportación al 100%
                    updateExportIndicator(100, 100);
                    System.out.println();
                    System.out.println();
                    
                } catch (IOException e) {
                    System.err.println(RED + "Error al exportar DDL de tabla " + tableName + ": " + e.getMessage() + RESET);
                }
            }

            // 4. Exportar Secuencias
            System.out.println(CYAN + "Exportando SECUENCIAS..." + RESET);
            exportSequences(conn, schema, userDir, encoding);

            // 5. Exportar Triggers
            System.out.println(CYAN + "Exportando TRIGGERS..." + RESET);
            exportTriggers(conn, schema, userDir, encoding);

            // 6. Exportar Funciones
            System.out.println(CYAN + "Exportando FUNCIONES..." + RESET);
            exportFunctions(conn, schema, userDir, encoding);

        } catch (SQLException e) {
            System.err.println(RED + "Error general: " + e.getMessage() + RESET);
        } finally {
            showCursor();
        }
    }

    private static void exportTableDDL(Connection conn, String schema, String tableName, File userDir, String encoding)
            throws SQLException, IOException {
        String ddlFileName = userDir + File.separator + getFileIndex() + tableName + "_DDL.sql";
        try (Statement stmt = conn.createStatement();
                ResultSet rs = stmt.executeQuery(
                    "SELECT DBMS_METADATA.GET_DDL('TABLE', '" + tableName + "', '" + schema + "') FROM DUAL")) {
            if (rs.next()) {
                String ddl = rs.getString(1);
                try (BufferedWriter writer = new BufferedWriter(new OutputStreamWriter(new FileOutputStream(ddlFileName), encoding))) {
                    writer.write(ddl);
                }
            }
        }
    }


    private static void exportTableDataBASE64File(Connection conn, String schema, String tableName, File userDir, String encoding) {
        String fileName = userDir + File.separator + getFileIndex() + tableName + "_inserts.sql";
        int updateExportIndicator = 0;
        try {
            // Contar total de filas
            int totalRows;
            try (Statement stmtCount = conn.createStatement();
                 ResultSet rsCount = stmtCount.executeQuery("SELECT COUNT(*) FROM " + schema + "." + tableName)) {
                rsCount.next();
                totalRows = rsCount.getInt(1);
            }

            System.out.print(YELLOW + "Progreso: [");
            int exported = 0;

            try (Statement stmt = conn.createStatement();
                 ResultSet rs = stmt.executeQuery("SELECT * FROM " + schema + "." + tableName);
                 BufferedWriter writer = new BufferedWriter(new OutputStreamWriter(new FileOutputStream(fileName), encoding))) {

                ResultSetMetaData meta = rs.getMetaData();
                int columnCount = meta.getColumnCount();

                while (rs.next()) {
                    StringBuilder insert = new StringBuilder("INSERT INTO " + schema + "." + tableName + " VALUES (");
                    for (int i = 1; i <= columnCount; i++) {
                        int columnType = meta.getColumnType(i);
                        String columnName = meta.getColumnName(i);
                        Object value = rs.getObject(i);

                        if (value != null) {
                            if (columnType == java.sql.Types.CLOB) {
                                Clob clob = rs.getClob(i);
                                String clobString = clobToString(clob);
                                String base64 = java.util.Base64.getEncoder().encodeToString(clobString.getBytes(encoding));
                                String clobFileName = String.format("CLOB_%s_%s_%05d.base64", tableName, columnName, exported + 1);
                                writeStringToFile(userDir, clobFileName, base64, encoding);
                                insert.append("'FILE:").append(clobFileName).append("'");
                            } else if (columnType == java.sql.Types.BLOB) {
                                Blob blob = rs.getBlob(i);
                                String base64 = java.util.Base64.getEncoder().encodeToString(blobToBytes(blob));
                                String blobFileName = String.format("BLOB_%s_%s_%05d.base64", tableName, columnName, exported + 1);
                                writeStringToFile(userDir, blobFileName, base64, encoding);
                                insert.append("'FILE:").append(blobFileName).append("'");
                            } else {
                                String strValue = value.toString().replace("'", "''");
                                insert.append("'").append(strValue).append("'");
                            }
                        } else {
                            insert.append("NULL");
                        }
                        if (i < columnCount) insert.append(", ");
                    }
                    insert.append(");\n");
                    writer.write(insert.toString());
                    exported++;

                    // Actualizar barra de progreso
                    if(updateExportIndicator == 0) {
                        updateExportIndicator(exported, totalRows);
                    }
                    updateExportIndicator++;
                    updateExportIndicator%=100;
                }
                // Ponemos la barra al 100%
                updateExportIndicator(100, 100);
            }
        } catch (SQLException | IOException e) {
            System.err.println(RED + "\nError procesando tabla " + tableName + ": " + e.getMessage() + RESET);
        }
    }

    // Escribe una cadena en un archivo externo
    private static void writeStringToFile(File userDir, String fileName, String content, String encoding) throws IOException {
        try (BufferedWriter bw = new BufferedWriter(new OutputStreamWriter(new FileOutputStream(new File(userDir, fileName)), encoding))) {
            bw.write(content);
        }
    }


    // Versión que añade un anexo "BASE64:" a los campos BLOB para tratar los inserts posteriormente
    private static void exportTableDataBASE64(Connection conn, String schema, String tableName, File userDir, String encoding) {
        String fileName = userDir + File.separator + getFileIndex() + tableName + "_inserts.sql";
        int updateExportIndicator = 0;
        try {
            // Contar total de filas
            int totalRows;
            try (Statement stmtCount = conn.createStatement();
                 ResultSet rsCount = stmtCount.executeQuery("SELECT COUNT(*) FROM " + schema + "." + tableName)) {
                rsCount.next();
                totalRows = rsCount.getInt(1);
            }

            System.out.print(YELLOW + "Progreso: [");
            int exported = 0;

            try (Statement stmt = conn.createStatement();
                 ResultSet rs = stmt.executeQuery("SELECT * FROM " + schema + "." + tableName);
                 BufferedWriter writer = new BufferedWriter(new OutputStreamWriter(new FileOutputStream(fileName), encoding))) {

                ResultSetMetaData meta = rs.getMetaData();
                int columnCount = meta.getColumnCount();

                while (rs.next()) {
                    StringBuilder insert = new StringBuilder("INSERT INTO " + schema + "." + tableName + " VALUES (");
                    for (int i = 1; i <= columnCount; i++) {
                        int columnType = meta.getColumnType(i);
                        Object value = rs.getObject(i);

                        if (value != null) {
                            if (columnType == java.sql.Types.CLOB) {
                                Clob clob = rs.getClob(i);
                                String clobString = clobToString(clob);
                                String base64 = java.util.Base64.getEncoder().encodeToString(clobString.getBytes(encoding));
                                insert.append("'BASE64:").append(base64).append("'");
                            } else if (columnType == java.sql.Types.BLOB) {
                                Blob blob = rs.getBlob(i);
                                String base64 = java.util.Base64.getEncoder().encodeToString(blobToBytes(blob));
                                insert.append("'BASE64BLOB:").append(base64).append("'");
                            } else {
                                String strValue = value.toString().replace("'", "''");
                                insert.append("'").append(strValue).append("'");
                            }
                        } else {
                            insert.append("NULL");
                        }
                        if (i < columnCount) insert.append(", ");
                    }
                    insert.append(");\n");
                    writer.write(insert.toString());
                    exported++;

                    // Actualizar barra de progreso
                    if(updateExportIndicator == 0) {
                        updateExportIndicator(exported, totalRows);
                    }
                    updateExportIndicator++;
                    updateExportIndicator%=100;
                }
                // Ponemos la barra al 100%
                updateExportIndicator(100, 100);
            }
        } catch (SQLException | IOException e) {
            System.err.println(RED + "\nError procesando tabla " + tableName + ": " + e.getMessage() + RESET);
        }
    }

    // Función auxiliar para leer un BLOB a byte[]
    private static byte[] blobToBytes(Blob blob) throws SQLException, IOException {
        try (InputStream is = blob.getBinaryStream();
             ByteArrayOutputStream baos = new ByteArrayOutputStream()) {
            byte[] buffer = new byte[4096];
            int n;
            while ((n = is.read(buffer)) != -1) {
                baos.write(buffer, 0, n);
            }
            return baos.toByteArray();
        }
    }


    // Version que exporta los CLOB a BASE64 Y modifica el insert para su decodificación
    private static void exportTableDataOracleBase64(Connection conn, String schema, String tableName, File userDir, String encoding) {
        String fileName = userDir + File.separator + getFileIndex() + tableName + "_inserts.sql";
        int updateExportIndicator = 0;
        try {
            // Contar total de filas
            int totalRows;
            try (Statement stmtCount = conn.createStatement();
                 ResultSet rsCount = stmtCount.executeQuery("SELECT COUNT(*) FROM " + schema + "." + tableName)) {
                rsCount.next();
                totalRows = rsCount.getInt(1);
            }

            System.out.print(YELLOW + "Progreso: [");
            int exported = 0;

            try (Statement stmt = conn.createStatement();
                 ResultSet rs = stmt.executeQuery("SELECT * FROM " + schema + "." + tableName);
                 BufferedWriter writer = new BufferedWriter(new OutputStreamWriter(new FileOutputStream(fileName), encoding))) {

                ResultSetMetaData meta = rs.getMetaData();
                int columnCount = meta.getColumnCount();

                while (rs.next()) {
                    StringBuilder insert = new StringBuilder("INSERT INTO " + schema + "." + tableName + " VALUES (");
                    for (int i = 1; i <= columnCount; i++) {
                        int columnType = meta.getColumnType(i);

                        Object value = rs.getObject(i);
                        if (value != null) {
                            if (columnType == java.sql.Types.CLOB) {
                                // Leer el CLOB y convertirlo a Base64
                                Clob clob = rs.getClob(i);
                                String clobString = clobToString(clob);
                                String base64 = java.util.Base64.getEncoder().encodeToString(clobString.getBytes(encoding));
                                // Insert especial para reconstruir el CLOB
                                insert.append("TO_CLOB(UTL_RAW.CAST_TO_VARCHAR2(UTL_ENCODE.BASE64_DECODE(UTL_RAW.CAST_TO_RAW('")
                                      .append(base64)
                                      .append("'))))");
                            } else {
                                String strValue = value.toString().replace("'", "''");
                                insert.append("'").append(strValue).append("'");
                            }
                        } else {
                            insert.append("NULL");
                        }
                        if (i < columnCount) insert.append(", ");
                    }
                    insert.append(");\n");
                    writer.write(insert.toString());
                    exported++;

                    // Actualizar barra de progreso
                    if(updateExportIndicator == 0) {
                        updateExportIndicator(exported, totalRows);
                    }
                    updateExportIndicator++;
                    updateExportIndicator%=100;
                }
                // Ponemos la barra al 100%
                updateExportIndicator(100, 100);
            }
        } catch (SQLException | IOException e) {
            System.err.println(RED + "\nError procesando tabla " + tableName + ": " + e.getMessage() + RESET);
        }
    }


    // Función auxiliar para leer un CLOB a String
    private static String clobToString(Clob clob) throws SQLException, IOException {
        StringBuilder sb = new StringBuilder();
        try (Reader reader = clob.getCharacterStream()) {
            char[] buffer = new char[4096];
            int n;
            while ((n = reader.read(buffer)) != -1) {
                sb.append(buffer, 0, n);
            }
        }
        return sb.toString();
    }


    // Funcion que no exporta los CLOB, si no que indica su referencia en la BBDD y en los insert generados
    private static void exportTableDataOracleRef(Connection conn, String schema, String tableName, File userDir, String encoding) {
        String fileName = userDir + File.separator + getFileIndex() + tableName + "_inserts.sql";
        int updateExportIndicator = 0;
        try {
            // Contar total de filas
            int totalRows;
            try (Statement stmtCount = conn.createStatement();
                 ResultSet rsCount = stmtCount.executeQuery("SELECT COUNT(*) FROM " + schema + "." + tableName)) {
                rsCount.next();
                totalRows = rsCount.getInt(1);
            }

            System.out.print(YELLOW + "Progreso: [");            
            int exported = 0;            

            try (Statement stmt = conn.createStatement();
                 ResultSet rs = stmt.executeQuery("SELECT * FROM " + schema + "." + tableName);
                 BufferedWriter writer = new BufferedWriter(new OutputStreamWriter(new FileOutputStream(fileName), encoding))) {

                ResultSetMetaData meta = rs.getMetaData();
                int columnCount = meta.getColumnCount();

                while (rs.next()) {
                    StringBuilder insert = new StringBuilder("INSERT INTO " + schema + "." + tableName + " VALUES (");
                    for (int i = 1; i <= columnCount; i++) {
                        Object value = rs.getObject(i);
                        if (value != null) {
                            String strValue = value.toString().replace("'", "''");
                            insert.append("'").append(strValue).append("'");
                        } else {
                            insert.append("NULL");
                        }
                        if (i < columnCount) insert.append(", ");
                    }
                    insert.append(");\n");
                    writer.write(insert.toString());
                    //System.out.print(GREEN + "." + RESET);
                    exported++;

                    // Actualizar barra de progreso
                    if(updateExportIndicator == 0) {
                        updateExportIndicator(exported, totalRows);
                    }

                    // Solo actualizamos la barra cada 100 inserts
                    updateExportIndicator++;
                    updateExportIndicator%=100;
                }

                // Ponemos la barra al 100%
                updateExportIndicator(100, 100);
            }
        } catch (SQLException | IOException e) {
            System.err.println(RED + "\nError procesando tabla " + tableName + ": " + e.getMessage() + RESET);
        }
    }

    private static void exportSequences(Connection conn, String schema, File userDir, String encoding) {
        try (PreparedStatement ps = conn.prepareStatement(
                "SELECT SEQUENCE_NAME FROM ALL_SEQUENCES WHERE SEQUENCE_OWNER = ?")) {
            ps.setString(1, schema.toUpperCase());
            try (ResultSet rs = ps.executeQuery()) {
                while (rs.next()) {
                    String seqName = rs.getString(1);
                    String ddl = getDDL(conn, "SEQUENCE", seqName, schema);
                    if (ddl != null) {
                        String fileName = userDir + File.separator + getFileIndex() + seqName + "_SEQ_DDL.sql";
                        writeToFile(fileName, ddl, encoding);
                    }
                }
            }
        } catch (SQLException | IOException e) {
            System.err.println(RED + "Error exportando secuencias: " + e.getMessage() + RESET);
        }
    }

    private static void exportTriggers(Connection conn, String schema, File userDir, String encoding) {
        try (PreparedStatement ps = conn.prepareStatement(
                "SELECT TRIGGER_NAME FROM ALL_TRIGGERS WHERE OWNER = ?")) {
            ps.setString(1, schema.toUpperCase());
            try (ResultSet rs = ps.executeQuery()) {
                while (rs.next()) {
                    String trgName = rs.getString(1);
                    String ddl = getDDL(conn, "TRIGGER", trgName, schema);
                    if (ddl != null) {
                        String fileName = userDir + File.separator + getFileIndex() + trgName + "_TRG_DDL.sql";
                        writeToFile(fileName, ddl, encoding);
                    }
                }
            }
        } catch (SQLException | IOException e) {
            System.err.println(RED + "Error exportando triggers: " + e.getMessage() + RESET);
        }
    }

    private static void exportFunctions(Connection conn, String schema, File userDir, String encoding) {
        try (PreparedStatement ps = conn.prepareStatement(
                "SELECT OBJECT_NAME FROM ALL_OBJECTS WHERE OWNER = ? AND OBJECT_TYPE = 'FUNCTION'")) {
            ps.setString(1, schema.toUpperCase());
            try (ResultSet rs = ps.executeQuery()) {
                while (rs.next()) {
                    String funcName = rs.getString(1);
                    String ddl = getDDL(conn, "FUNCTION", funcName, schema);
                    if (ddl != null) {
                        String fileName = userDir + File.separator + getFileIndex() + funcName + "_FUNC_DDL.sql";
                        writeToFile(fileName, ddl, encoding);
                    }
                }
            }
        } catch (SQLException | IOException e) {
            System.err.println(RED + "Error exportando funciones: " + e.getMessage() + RESET);
        }
    }

    private static String getDDL(Connection conn, String objectType, String objectName, String schema) {
        try (PreparedStatement ps = conn.prepareStatement(
                "SELECT DBMS_METADATA.GET_DDL(?, ?, ?) FROM DUAL")) {
            ps.setString(1, objectType);
            ps.setString(2, objectName);
            ps.setString(3, schema);
            try (ResultSet rs = ps.executeQuery()) {
                if (rs.next()) {
                    return rs.getString(1);
                }
            }
        } catch (SQLException e) {
            // Puede que algunos objetos no tengan DDL exportable (por ejemplo, si son del sistema)
        }
        return null;
    }

    private static void writeToFile(String fileName, String content, String encoding) throws IOException {
        try (BufferedWriter writer = new BufferedWriter(new OutputStreamWriter(new FileOutputStream(fileName), encoding))) {
            writer.write(content);
        }
    }

     private static String getFileIndex() {
        return String.format("%07d", fileNumber++) + "_";
    }

    private static void updateExportIndicator(int exported, int totalRows) {
        int barWidth = 50;
        int progress = 0;
        int percentage = 0;

        try {
            progress = (int) ((double) exported / totalRows * barWidth);
            percentage = (exported * 100 / totalRows);
        } catch(Exception e) {
            progress = 0;
            percentage = 0;
        }

        System.out.print("\r" + GREEN + "Progreso: [");
        for (int i = 0; i < barWidth; i++) {
            System.out.print(i < progress ? BG_GREEN + BLACK + "=" : RESET + " ");
        }
        System.out.print(RESET + GREEN + "] " + percentage + "% " + RESET);
    }

    private static Properties loadConfig() {
        Properties config = new Properties();
        try (InputStream input = new FileInputStream(CONFIG_FILE)) {
            config.load(input);
            return config;
        } catch (IOException e) {
            System.err.println(RED + "No se pudo cargar el archivo de configuración " + CONFIG_FILE + RESET);
            return null;
        }
    }

    private static void hideCursor() {
        System.out.print("\u001B[?25l");
        System.out.flush();
    }

    private static void showCursor() {
        System.out.print("\u001B[?25h");
        System.out.flush();
    }
}
