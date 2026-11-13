package app;

import java.sql.Statement;

public class OrderDao {
    private Statement stmt;

    public String find(String status) throws Exception {
        String filter = buildFilter(status);
        return stmt.executeQuery("SELECT * FROM orders WHERE " + filter).toString();
    }

    private String buildFilter(String status) {
        return "status = '" + status + "'";
    }

    public String safe(int id) throws Exception {
        return stmt.executeQuery("SELECT * FROM orders WHERE id = 1").toString();
    }
}
