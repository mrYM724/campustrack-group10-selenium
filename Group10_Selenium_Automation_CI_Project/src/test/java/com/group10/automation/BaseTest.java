package com.group10.automation;

import org.openqa.selenium.*;
import org.openqa.selenium.chrome.ChromeDriver;
import org.openqa.selenium.chrome.ChromeOptions;
import org.openqa.selenium.support.ui.ExpectedConditions;
import org.openqa.selenium.support.ui.WebDriverWait;
import org.testng.Assert;
import org.testng.annotations.AfterMethod;
import org.testng.annotations.BeforeMethod;

import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Duration;
import java.util.HashMap;
import java.util.Map;

public abstract class BaseTest {
    private static final ThreadLocal<WebDriver> DRIVERS = new ThreadLocal<>();
    protected WebDriver driver;
    protected WebDriverWait wait;
    protected String baseUrl;
    protected Path downloadDirectory;

    public static WebDriver activeDriver() { return DRIVERS.get(); }

    @BeforeMethod(alwaysRun = true)
    public void setUp() throws Exception {
        baseUrl = System.getProperty("baseUrl", "http://127.0.0.1:8000").replaceAll("/+$", "");
        String token = System.getenv().getOrDefault("TEST_TOKEN", "local-ci-demo-token");
        HttpRequest reset = HttpRequest.newBuilder(URI.create(baseUrl + "/api/test/reset"))
            .header("X-Test-Token", token).POST(HttpRequest.BodyPublishers.noBody()).build();
        HttpResponse<String> response = HttpClient.newHttpClient().send(reset, HttpResponse.BodyHandlers.ofString());
        Assert.assertEquals(response.statusCode(), 200,
            "Test database reset failed. Start server with TEST_MODE=1 and matching TEST_TOKEN. Response: " + response.body());
        downloadDirectory = Files.createTempDirectory("campustrack-download-").toAbsolutePath();
        ChromeOptions options = new ChromeOptions();
        if (Boolean.parseBoolean(System.getProperty("headless", "true"))) {
            options.addArguments("--headless=new");
        }
        options.addArguments("--window-size=1440,1000", "--disable-dev-shm-usage", "--no-sandbox");
        Map<String, Object> prefs = new HashMap<>();
        prefs.put("download.default_directory", downloadDirectory.toString());
        prefs.put("download.prompt_for_download", false);
        prefs.put("download.directory_upgrade", true);
        prefs.put("safebrowsing.enabled", true);
        options.setExperimentalOption("prefs", prefs);
        driver = new ChromeDriver(options);
        DRIVERS.set(driver);
        wait = new WebDriverWait(driver, Duration.ofSeconds(15));
    }

    @AfterMethod(alwaysRun = true)
    public void tearDown() {
        if (driver != null) { driver.quit(); driver = null; }
        DRIVERS.remove();
    }

    protected WebElement el(String id) { return wait.until(ExpectedConditions.visibilityOfElementLocated(By.id(id))); }
    protected WebElement find(By selector) { return wait.until(ExpectedConditions.visibilityOfElementLocated(selector)); }
    protected void click(String id) { wait.until(ExpectedConditions.elementToBeClickable(By.id(id))).click(); }
    protected void type(String id, String value) { WebElement field = el(id); field.clear(); field.sendKeys(value); }

    protected void login(String username, String password) {
        driver.get(baseUrl + ("admin".equals(username) ? "/admin/login" : "/student/login"));
        type("login-username", username);
        type("login-password", password);
        click("login-submit");
        wait.until(ExpectedConditions.visibilityOfElementLocated(By.id("stat-total")));
        wait.until(d -> "25".equals(d.findElement(By.id("stat-total")).getText()));
    }
    protected void loginAdmin() { login("admin", "Admin@123"); }
    protected void loginUser() { login("student", "Student@123"); }

    protected void search(String query) {
        type("search-input", query);
        click("search-button");
        wait.until(d -> d.findElement(By.id("total-summary")).getText().matches("\\d+ matching records"));
    }

    protected void awaitRow(String code) {
        wait.until(ExpectedConditions.visibilityOfElementLocated(By.cssSelector("#record-rows tr[data-code='" + code + "']")));
    }

    protected void awaitCount(int number) {
        wait.until(d -> Integer.toString(number).equals(d.findElement(By.id("stat-total")).getText()));
    }

    protected void openAddRecord() {
        click("add-record-btn");
        wait.until(ExpectedConditions.visibilityOfElementLocated(By.id("field-code")));
    }

    protected void fillRecord(String code, String name, String course, String date, String status) {
        type("field-code", code);
        type("field-name", name);
        type("field-course", course);
        WebElement dateField = el("field-date");
        // Date input uses JS value assignment and bubbles an input event, avoiding OS-locale typing variance.
        ((JavascriptExecutor)driver).executeScript(
            "arguments[0].value=arguments[1];arguments[0].dispatchEvent(new Event('input',{bubbles:true}));",
            dateField, date);
        new org.openqa.selenium.support.ui.Select(el("field-status")).selectByVisibleText(status);
    }

    protected void addRecord(String code, String name) {
        openAddRecord();
        fillRecord(code, name, "DevOps Lab", "2026-10-21", "Present");
        click("save-record");
        awaitRow(code);
    }
}
