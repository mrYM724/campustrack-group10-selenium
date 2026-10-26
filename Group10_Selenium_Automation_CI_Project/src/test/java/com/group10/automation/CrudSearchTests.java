package com.group10.automation;

import org.openqa.selenium.By;
import org.openqa.selenium.WebElement;
import org.openqa.selenium.support.ui.Select;
import org.testng.Assert;
import org.testng.annotations.Test;

public class CrudSearchTests extends BaseTest {
    @Test(description = "TC07: Admin creates a new student attendance record")
    public void createAttendanceRecord() {
        loginAdmin();
        addRecord("ST801", "QA Demo Student");
        awaitCount(26);
        Assert.assertEquals(driver.findElement(By.cssSelector("tr[data-code='ST801'] td.student-name")).getText(), "QA Demo Student");
    }
    @Test(description = "TC08: Admin edits the student and attendance status")
    public void updateAttendanceRecord() {
        loginAdmin();
        search("ST001");
        awaitRow("ST001");
        driver.findElement(By.cssSelector("tr[data-code='ST001'] button[data-action='edit']")).click();
        type("field-name", "Aarav Updated");
        new Select(el("field-status")).selectByVisibleText("Absent");
        click("save-record");
        awaitRow("ST001");
        Assert.assertEquals(driver.findElement(By.cssSelector("tr[data-code='ST001'] td.student-name")).getText(), "Aarav Updated");
        Assert.assertEquals(driver.findElement(By.cssSelector("tr[data-code='ST001'] .status-pill")).getText(), "Absent");
    }
    @Test(description = "TC09: Admin deletes a record and it disappears from search")
    public void deleteAttendanceRecord() {
        loginAdmin();
        search("ST001");
        awaitRow("ST001");
        driver.findElement(By.cssSelector("tr[data-code='ST001'] button[data-action='delete']")).click();
        wait.until(d -> { try { d.switchTo().alert().accept(); return true; } catch (Exception x) { return false; } });
        awaitCount(24);
        wait.until(d -> d.findElements(By.cssSelector("tr[data-code='ST001']")).isEmpty());
        Assert.assertTrue(el("record-rows").getText().contains("No matching"));
    }
    @Test(description = "TC10: Search returns the correct single student - intentional regression detector")
    public void searchReturnsOnlyMatchingStudent() {
        loginAdmin();
        search("Aarav Mehta");
        wait.until(d -> "1 matching records".equals(d.findElement(By.id("total-summary")).getText()));
        Assert.assertEquals(driver.findElements(By.cssSelector("#record-rows tr[data-code]")).size(), 1);
        Assert.assertEquals(driver.findElement(By.cssSelector("#record-rows .student-name")).getText(), "Aarav Mehta");
    }
    @Test(description = "TC11: Searching a missing student displays an empty state")
    public void searchNoResults() {
        loginAdmin();
        search("THIS_NAME_DOES_NOT_EXIST");
        wait.until(d -> "0 matching records".equals(d.findElement(By.id("total-summary")).getText()));
        Assert.assertTrue(el("record-rows").getText().contains("No matching"));
    }
}
