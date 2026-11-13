package app;

import javax.servlet.http.HttpServletRequest;

public class OrderController {
    private final OrderDao dao = new OrderDao();

    public String show(HttpServletRequest request) throws Exception {
        String status = request.getParameter("status");
        return dao.find(status);
    }

    public String showDirect(HttpServletRequest request, java.sql.Statement stmt) throws Exception {
        String id = request.getParameter("id");
        return stmt.executeQuery("SELECT * FROM orders WHERE id = " + id).toString();
    }
}
