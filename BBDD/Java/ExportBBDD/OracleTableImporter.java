/**
 * OracleTableImporter
 *
 * Importa el contenido exportado por OracleTableExporter en el siguiente orden:
 * 1. DDL de tablas
 * 2. Secuencias
 * 3. Inserts (con soporte para BLOB/CLOB en ficheros externos)
 * 4. Funciones
 * 5. Triggers
 */

import java.io.*;
import java.sql.*;
import java.util.*;
import java.util.regex.*;

public class OracleTableImporter {
    private static final String CONFIG_FILE = "OracleTableExporter.properties";
    private static final Pattern FILE_REF_PATTERN = Pattern.compile("'FILE:(BLOB|CLOB)_(.+?)_(.+?)_(\\d{5})\\.base64'");

    public static void main(String[] args) {
        Properties config = loadConfig();
        if (config == null) return;

        String url = config.getProperty("jdbc.url");
        String user = config.getProperty("jdbc.user");
        String password = config.getProperty("jdbc.password");
        String schema = config.getProperty("jdbc.schema", user);
        String encoding = config.getProperty("encoding", "UTF-8");

        File userDir = new File(schema);
        if (!userDir.exists() || !userDir.isDirectory()) {
            System.err.println("No existe la carpeta de datos: " + schema);
            return;
        }

        try (Connection conn = DriverManager.getConnection(url, user, password)) {
            // 1. Importar DDL de tablas
            System.out.println("Importando DDL de tablas...");
            importarArchivosPorPatron(conn, userDir, "_DDL.sql", encoding);

            // 2. Importar secuencias
            System.out.println("Importando secuencias...");
            importarArchivosPorPatron(conn, userDir, "_SEQ_DDL.sql", encoding);

            // 3. Importar datos (inserts)
            System.out.println("Importando datos (inserts)...");
            importarInserts(conn, userDir, encoding);

            // 4. Importar funciones
            System.out.println("Importando funciones...");
            importarArchivosPorPatron(conn, userDir, "_FUNC_DDL.sql", encoding);

            // 5. Importar triggers
            System.out.println("Importando triggers...");
            importarArchivosPorPatron(conn, userDir, "_TRG_DDL.sql", encoding);

            System.out.println("Importación finalizada.");
        } catch (SQLException e) {
            System.err.println("Error de conexión o importación: " + e.getMessage());
        }
    }

    private static void importarArchivosPorPatron(Connection conn, File userDir, String sufijo, String encoding) {
        File[] files = userDir.listFiles((dir, name) -> name.endsWith(sufijo));
        if (files == null) return;
        Arrays.sort(files);
        for (File file : files) {
            importarScript(conn, file, encoding);
        }
    }

    private static void importarScript(Connection conn, File scriptFile, String encoding) {
        try (BufferedReader reader = new BufferedReader(new InputStreamReader(new FileInputStream(scriptFile), encoding))) {
            StringBuilder sb = new StringBuilder();
            String line;
            while ((line = reader.readLine()) != null) {
                sb.append(line).append('\n');
            }
            String sql = sb.toString();
            try (Statement stmt = conn.createStatement()) {
                stmt.execute(sql);
                System.out.println("Importado: " + scriptFile.getName());
            }
        } catch (IOException | SQLException e) {
            System.err.println("Error importando " + scriptFile.getName() + ": " + e.getMessage());
        }
    }

    private static void importarInserts(Connection conn, File userDir, String encoding) {
        File[] insertFiles = userDir.listFiles((dir, name) -> name.endsWith("_inserts.sql"));
        if (insertFiles == null) return;
        Arrays.sort(insertFiles);
        for (File insertFile : insertFiles) {
            System.out.println("Importando datos desde: " + insertFile.getName());
            importTableInserts(conn, userDir, insertFile, encoding);
        }
    }

    private static void importTableInserts(Connection conn, File userDir, File insertFile, String encoding) {
        try (BufferedReader reader = new BufferedReader(new InputStreamReader(new FileInputStream(insertFile), encoding))) {
            String line;
            while ((line = reader.readLine()) != null) {
                if (line.trim().isEmpty()) continue;

                // Detectar si hay referencias a archivos BLOB/CLOB
                Matcher matcher = FILE_REF_PATTERN.matcher(line);
                if (matcher.find()) {
                    // Hay al menos un campo BLOB/CLOB en este insert
                    ejecutarInsertConFicheros(conn, userDir, line, encoding);
                } else {
                    // Insert normal, ejecutar tal cual
                    try (Statement stmt = conn.createStatement()) {
                        stmt.executeUpdate(line);
                    }
                }
            }
        } catch (IOException | SQLException e) {
            System.err.println("Error importando desde " + insertFile.getName() + ": " + e.getMessage());
        }
    }

    private static void ejecutarInsertConFicheros(Connection conn, File userDir, String insertLine, String encoding) throws SQLException, IOException {
        int intoIdx = insertLine.indexOf("INTO ");
        int valuesIdx = insertLine.indexOf(" VALUES ");
        if (intoIdx == -1 || valuesIdx == -1) throw new SQLException("Formato de insert no reconocido: " + insertLine);

        String tabla = insertLine.substring(intoIdx + 5, valuesIdx).trim();
        String valores = insertLine.substring(valuesIdx + 8, insertLine.lastIndexOf(')')).trim();
        valores = valores.substring(1); // quitar el primer paréntesis

        List<String> valueList = splitValues(valores);

        StringBuilder sql = new StringBuilder("INSERT INTO ").append(tabla).append(" VALUES (");
        for (int i = 0; i < valueList.size(); i++) {
            sql.append("?");
            if (i < valueList.size() - 1) sql.append(", ");
        }
        sql.append(")");

        try (PreparedStatement pstmt = conn.prepareStatement(sql.toString())) {
            for (int i = 0; i < valueList.size(); i++) {
                String val = valueList.get(i).trim();
                Matcher matcher = FILE_REF_PATTERN.matcher(val);
                if (matcher.matches()) {
                    String tipo = matcher.group(1);
                    String tablaRef = matcher.group(2);
                    String campo = matcher.group(3);
                    String idReg = matcher.group(4);
                    String fileName = tipo + "_" + tablaRef + "_" + campo + "_" + idReg + ".base64";
                    File dataFile = new File(userDir, fileName);
                    if (!dataFile.exists()) throw new IOException("No se encuentra el fichero: " + fileName);

                    byte[] decoded = Base64.getDecoder().decode(readFileToString(dataFile, encoding));
                    if (tipo.equals("BLOB")) {
                        pstmt.setBlob(i + 1, new ByteArrayInputStream(decoded));
                    } else if (tipo.equals("CLOB")) {
                        String clobStr = new String(decoded, encoding);
                        pstmt.setClob(i + 1, new StringReader(clobStr));
                    }
                } else if (val.equalsIgnoreCase("NULL")) {
                    pstmt.setNull(i + 1, Types.NULL);
                } else {
                    // Quitar las comillas simples
                    if (val.startsWith("'") && val.endsWith("'")) {
                        val = val.substring(1, val.length() - 1).replace("''", "'");
                    }
                    pstmt.setString(i + 1, val);
                }
            }
            pstmt.executeUpdate();
        }
    }

    private static List<String> splitValues(String values) {
        List<String> result = new ArrayList<>();
        StringBuilder sb = new StringBuilder();
        boolean inQuotes = false;
        for (int i = 0; i < values.length(); i++) {
            char c = values.charAt(i);
            if (c == '\'') inQuotes = !inQuotes;
            if (c == ',' && !inQuotes) {
                result.add(sb.toString().trim());
                sb.setLength(0);
            } else {
                sb.append(c);
            }
        }
        if (sb.length() > 0) result.add(sb.toString().trim());
        return result;
    }

    private static String readFileToString(File file, String encoding) throws IOException {
        try (BufferedReader br = new BufferedReader(new InputStreamReader(new FileInputStream(file), encoding))) {
            StringBuilder sb = new StringBuilder();
            String line;
            while ((line = br.readLine()) != null) sb.append(line);
            return sb.toString();
        }
    }

    private static Properties loadConfig() {
        Properties config = new Properties();
        try (InputStream input = new FileInputStream(CONFIG_FILE)) {
            config.load(input);
            return config;
        } catch (IOException e) {
            System.err.println("No se pudo cargar el archivo de configuración " + CONFIG_FILE);
            return null;
        }
    }
}
