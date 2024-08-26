import java.sql.Connection;
import java.sql.DriverManager;
import java.sql.ResultSet;
import java.sql.Statement;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import org.json.JSONArray;
import org.json.JSONObject;



public class SchemaReader {
    public static Map<String, List<Map<String, String>>> getOracleSchema(String url, String username, String password, String schemaName) throws Exception {
        Connection connection = DriverManager.getConnection(url, username, password);
        Statement statement = connection.createStatement();

        String query = ""
                + "SELECT b.TABLE_NAME || '(' || NVL(b.COMMENTS, '') || ')' AS TAB_NAME " 
                + " , a.COLUMN_NAME AS COL_NAME"
                + " , a.DATA_TYPE AS COL_TYPE"
                + " , c.COMMENTS AS COL_COMMENT"
                + " FROM ALL_TAB_COLUMNS a, user_tab_comments b, user_col_comments c \n"
                + " WHERE 1=1 \n"
                + " AND a.TABLE_NAME = b.TABLE_NAME \n"
                + " AND a.TABLE_NAME = c.TABLE_NAME(+) \n"
                + " AND a.COLUMN_NAME = c.COLUMN_NAME(+) \n"
//                + " AND b.TABLE_NAME = '" + schemaName.toUpperCase() + "' \n"
                + " ORDER BY b.TABLE_NAME, a.COLUMN_NAME";

        ResultSet rs = statement.executeQuery(query);

        Map<String, List<Map<String, String>>> schema = new HashMap<>();

        while (rs.next()) {
            String tabName = rs.getString("TAB_NAME");
            String colName = rs.getString("COL_NAME");
            String dataType = rs.getString("COL_TYPE");
            String colComment = rs.getString("COL_COMMENT");

            Map<String, String> columnInfo = new HashMap<>();
            columnInfo.put("NAME", colName);
            columnInfo.put("TYPE", dataType);
            columnInfo.put("COMMENT", colComment != null ? colComment : "");

            schema.computeIfAbsent(tabName, k -> new ArrayList<>()).add(columnInfo);
        }

        rs.close();
        connection.close();
        return schema;
    }

    public static String formatSchemaForPrompt(Map<String, List<Map<String, String>>> schema) {
        StringBuilder formatted = new StringBuilder("Tables:\n");

        for (String table : schema.keySet()) {
            formatted.append(" - ").append(table).append(":\n");
            formatted.append(schema.get(table).stream()
                .map(e -> e.get("NAME") + " (" + e.get("TYPE") + "): " + e.get("COMMENT"))
                .toArray(String[]::new));
            formatted.append("\n");
        }

        return formatted.toString();
    }

    public static String convertSchemaToJson(Map<String, List<Map<String, String>>> schema) {
        JSONArray tablesArray = new JSONArray();

        for (String tableName : schema.keySet()) {
            JSONObject tableObject = new JSONObject();
            tableObject.put("table_name", tableName);
            tableObject.put("columns", schema.get(tableName));
            tablesArray.put(tableObject);
        }

        return tablesArray.toString(4);
    }

    public static void main(String[] args) throws Exception {
        String oracleUrl = "jdbc:oracle:thin:@172.16.3.3:1527:ZGDV";
        String username = "zcgmst";
        String password = "rogkfkav";

        Map<String, List<Map<String, String>>> oracleSchema = getOracleSchema(oracleUrl, username, password, "");

        System.out.println(convertSchemaToJson(oracleSchema));
    }
}
