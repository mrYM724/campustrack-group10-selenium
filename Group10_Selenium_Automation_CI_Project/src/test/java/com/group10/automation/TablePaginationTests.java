package com.group10.automation;

import org.openqa.selenium.By;
import org.testng.Assert;
import org.testng.annotations.Test;

public class TablePaginationTests extends BaseTest {
    @Test(description = "TC12: Table shows correct student identity, course, and exactly ten rows on page 1")
    public void tableContainsCorrectData() {
        loginAdmin();
        awaitRow("ST001");
        Assert.assertEquals(driver.findElements(By.cssSelector("#record-rows tr[data-code]")).size(), 10);
        Assert.assertEquals(driver.findElement(By.cssSelector("tr[data-code='ST001'] td.student-name")).getText(), "Aarav Mehta");
        Assert.assertTrue(driver.findElement(By.cssSelector("tr[data-code='ST001']")).getText().contains("Data Structures"));
        Assert.assertEquals(el("page-info").getText(), "Page 1 of 3");
    }
    @Test(description = "TC13: Next and Previous pagination show the correct record ranges")
    public void paginationNextAndPrevious() {
        loginAdmin();
        awaitRow("ST001");
        click("next-page");
        awaitRow("ST011");
        Assert.assertEquals(el("page-info").getText(), "Page 2 of 3");
        Assert.assertTrue(driver.findElements(By.cssSelector("tr[data-code='ST001']")).isEmpty());
        click("prev-page");
        awaitRow("ST001");
        Assert.assertEquals(el("page-info").getText(), "Page 1 of 3");
    }
    @Test(description = "TC14: User role can view the same attendance table but no edit buttons")
    public void viewerCannotEditTable() {
        loginUser();
        awaitRow("ST001");
        Assert.assertTrue(driver.findElements(By.cssSelector("button[data-action='edit']")).isEmpty());
        Assert.assertTrue(driver.findElements(By.id("add-record-btn")).isEmpty());
    }
}
