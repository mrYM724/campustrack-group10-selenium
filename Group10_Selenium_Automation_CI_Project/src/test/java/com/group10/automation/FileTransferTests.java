package com.group10.automation;

import org.openqa.selenium.By;
import org.testng.Assert;
import org.testng.annotations.Test;

import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Duration;

public class FileTransferTests extends BaseTest {
    @Test(description = "TC15: Valid CSV upload creates two records through the browser")
    public void validCsvUpload() throws Exception {
        loginAdmin();
        Path csv = Files.createTempFile("attendance-import-", ".csv");
        Files.writeString(csv, "student_code,student_name,course,attendance_date,status,notes\nST901,Import Alpha,DevOps Lab,2026-10-21,Present,ok\nST902,Import Beta,Computer Networks,2026-10-21,Absent,ok\n");
        el("csv-file").sendKeys(csv.toAbsolutePath().toString());
        click("upload-btn");
        awaitCount(27);
        search("ST901");
        awaitRow("ST901");
        Assert.assertTrue(el("record-rows").getText().contains("Import Alpha"));
    }
    @Test(description = "TC16: Invalid CSV schema is rejected and database stays unchanged")
    public void invalidCsvUploadRejected() throws Exception {
        loginAdmin();
        Path csv = Files.createTempFile("bad-attendance-", ".csv");
        Files.writeString(csv, "wrong_column,bad_field\nABC,XYZ\n");
        el("csv-file").sendKeys(csv.toAbsolutePath().toString());
        click("upload-btn");
        wait.until(d -> d.findElement(By.id("toast")).getText().contains("Missing required CSV columns"));
        Assert.assertEquals(el("stat-total").getText(), "25");
    }
    @Test(description = "TC17: Browser downloads a complete attendance CSV report with correct records")
    public void reportDownloadsCorrectCsv() throws Exception {
        loginAdmin();
        awaitRow("ST001");
        click("download-btn");
        Path csvFile = downloadDirectory.resolve("attendance_report.csv");
        wait.withTimeout(Duration.ofSeconds(20)).until(d -> Files.exists(csvFile) && csvFile.toFile().length() > 50);
        String contents = Files.readString(csvFile, StandardCharsets.UTF_8);
        Assert.assertTrue(contents.contains("student_code,student_name,course,attendance_date,status,notes"));
        Assert.assertTrue(contents.contains("ST001,Aarav Mehta"));
        Assert.assertTrue(contents.contains("ST025,Aditi Sethi"));
    }
    @Test(description = "TC18: Read-only user may download attendance report")
    public void userCanDownloadReport() throws Exception {
        loginUser();
        click("download-btn");
        Path csvFile = downloadDirectory.resolve("attendance_report.csv");
        wait.withTimeout(Duration.ofSeconds(20)).until(d -> Files.exists(csvFile) && csvFile.toFile().length() > 50);
        Assert.assertTrue(Files.readString(csvFile, StandardCharsets.UTF_8).contains("ST001"));
    }
}
