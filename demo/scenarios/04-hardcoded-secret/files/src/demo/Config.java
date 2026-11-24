package demo;

public final class Config {
    private Config() {}

    // Ví dụ trong tài liệu của AWS, không phải khóa thật.
    public static final String ACCESS_KEY = "AKIAIOSFODNN7EXAMPLE";
    public static final String DB_PASSWORD = "Sup3rS3cretPassw0rd!";
    public static final String FROM_ENV = System.getenv("DB_PASSWORD");
}
