package com.group10.automation;

import com.aventstack.extentreports.ExtentReports;
import com.aventstack.extentreports.ExtentTest;
import com.aventstack.extentreports.MediaEntityBuilder;
import com.aventstack.extentreports.reporter.ExtentSparkReporter;
import org.openqa.selenium.OutputType;
import org.openqa.selenium.TakesScreenshot;
import org.openqa.selenium.WebDriver;
import org.testng.ITestContext;
import org.testng.ITestListener;
import org.testng.ITestResult;

import java.nio.file.Files;
import java.nio.file.Path;

/** HTML reporting, test status, and screenshot evidence for failed cases. */
public class ExtentListener implements ITestListener {
    private static final ExtentReports REPORT = new ExtentReports();
    private static final ThreadLocal<ExtentTest> ACTIVE_TEST = new ThreadLocal<>();
    static {
        try { Files.createDirectories(Path.of("target", "extent-report")); }
        catch (Exception ex) { throw new ExceptionInInitializerError(ex); }
        ExtentSparkReporter spark = new ExtentSparkReporter("target/extent-report/index.html");
        spark.config().setDocumentTitle("Group No. 10 | Selenium Automation Results");
        spark.config().setReportName("CampusTrack Automated Regression Suite");
        REPORT.attachReporter(spark);
        REPORT.setSystemInfo("Project", "CampusTrack Attendance Management");
        REPORT.setSystemInfo("Framework", "Selenium + TestNG + Maven + ExtentReports");
    }
    @Override public void onTestStart(ITestResult result) {
        ACTIVE_TEST.set(REPORT.createTest(result.getMethod().getMethodName(), result.getMethod().getDescription()));
    }
    @Override public void onTestSuccess(ITestResult result) {
        if (ACTIVE_TEST.get() != null) ACTIVE_TEST.get().pass("All assertions passed");
        ACTIVE_TEST.remove();
    }
    @Override public void onTestFailure(ITestResult result) {
        ExtentTest test = ACTIVE_TEST.get();
        if (test == null) { test = REPORT.createTest(result.getName()); }
        test.fail(result.getThrowable());
        WebDriver driver = BaseTest.activeDriver();
        if (driver instanceof TakesScreenshot) {
            try {
                String png = ((TakesScreenshot) driver).getScreenshotAs(OutputType.BASE64);
                test.fail("Screenshot captured at failure", MediaEntityBuilder.createScreenCaptureFromBase64String(png).build());
                Path dir = Path.of("target", "screenshots");
                Files.createDirectories(dir);
                byte[] raw = java.util.Base64.getDecoder().decode(png);
                Files.write(dir.resolve(result.getName() + "-failure.png"), raw);
            } catch (Exception ignored) { test.warning("Screenshot was unavailable"); }
        }
        ACTIVE_TEST.remove();
    }
    @Override public void onTestSkipped(ITestResult result) {
        ExtentTest test = ACTIVE_TEST.get();
        if (test == null) test = REPORT.createTest(result.getName());
        test.skip(result.getThrowable()); ACTIVE_TEST.remove();
    }
    @Override public void onFinish(ITestContext context) { REPORT.flush(); }
}
