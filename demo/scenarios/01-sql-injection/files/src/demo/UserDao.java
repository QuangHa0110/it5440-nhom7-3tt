package demo;

import java.sql.Connection;
import java.sql.PreparedStatement;
import java.sql.ResultSet;
import java.sql.SQLException;
import java.sql.Statement;

public class UserDao {
    private final Connection conn;

    public UserDao(Connection conn) {
        this.conn = conn;
    }

    public String findName(int id) throws SQLException {
        try (PreparedStatement ps = conn.prepareStatement("SELECT name FROM users WHERE id = ?")) {
            ps.setInt(1, id);
            try (ResultSet rs = ps.executeQuery()) {
                return rs.next() ? rs.getString(1) : null;
            }
        }
    }

    public String searchByName(String name) throws SQLException {
        Statement st = conn.createStatement();
        String sql = "SELECT name FROM users WHERE name = '" + name + "'";
        ResultSet rs = st.executeQuery(sql);
        return rs.next() ? rs.getString(1) : null;
    }
}
