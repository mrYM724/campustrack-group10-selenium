package com.group10.automation;

import org.openqa.selenium.By;
import org.testng.Assert;
import org.testng.annotations.Test;

public class LoginRoleTests extends BaseTest {
    @Test(description = "TC01: Valid administrator login opens the attendance dashboard")
    public void adminLoginSucceeds() {
        loginAdmin();
        Assert.assertEquals(driver.findElement(By.tagName("body")).getAttribute("data-role"), "admin");
        Assert.assertTrue(driver.findElement(By.id("account-name")).getText().contains("Administrator"));
    }
    @Test(description = "TC02: Normal user can log in with read-only access")
    public void normalUserLoginSucceeds() {
        loginUser();
        Assert.assertEquals(driver.findElement(By.tagName("body")).getAttribute("data-role"), "user");
        Assert.assertTrue(driver.findElement(By.className("readonly-label")).isDisplayed());
    }
    @Test(description = "TC03: Admin sees the protected administrative console")
    public void adminCanOpenAdminConsole() {
        loginAdmin();
        Assert.assertEquals(driver.findElements(By.id("admin-nav")).size(), 1);
        click("admin-nav");
        Assert.assertEquals(el("admin-heading").getText(), "Admin console");
    }
    @Test(description = "TC04: User cannot see or visit the administrator page even with a direct URL")
    public void normalUserCannotAccessAdminPage() {
        loginUser();
        Assert.assertTrue(driver.findElements(By.id("admin-nav")).isEmpty());
        driver.get(baseUrl + "/admin");
        Assert.assertTrue(driver.getPageSource().contains("Admin role required"), "Direct admin URL must be refused by server");
    }
    @Test(description = "TC05: Server rejects a normal user's attempt to create a record")
    public void normalUserCannotCreateRecords() {
        loginUser();
        Object status = ((org.openqa.selenium.JavascriptExecutor)driver).executeAsyncScript(
            "const done=arguments[arguments.length-1];fetch('/api/records',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({student_code:'ST999',student_name:'Unauthorized User',course:'DevOps Lab',attendance_date:'2026-10-21',status:'Present',notes:''})}).then(r=>done(r.status)).catch(e=>done(e.toString()));");
        Assert.assertEquals(((Number)status).intValue(), 403);
    }
    @Test(description = "TC19: Separate portal choice has no combined sign-in form")
    public void portalChoiceSeparatesRoles() {
        driver.get(baseUrl + "/login");
        Assert.assertEquals(driver.findElements(By.id("login-form")).size(), 0);
        Assert.assertEquals(driver.findElements(By.id("admin-portal-link")).size(), 1);
        Assert.assertEquals(driver.findElements(By.id("student-portal-link")).size(), 1);
        click("student-portal-link");
        Assert.assertTrue(driver.getCurrentUrl().endsWith("/student/login"));
        Assert.assertTrue(driver.getPageSource().contains("Student sign in"));
    }
    @Test(description = "TC20: Student credentials rejected on administrator portal")
    public void studentCannotSignInOnAdminPortal() {
        driver.get(baseUrl + "/admin/login");
        type("login-username", "student");
        type("login-password", "Student@123");
        click("login-submit");
        Assert.assertTrue(el("login-error").getText().contains("Invalid username"));
        Assert.assertTrue(driver.getCurrentUrl().endsWith("/admin/login"));
    }
    @Test(description = "TC21: Administrator credentials rejected on student portal")
    public void adminCannotSignInOnStudentPortal() {
        driver.get(baseUrl + "/student/login");
        type("login-username", "admin");
        type("login-password", "Admin@123");
        click("login-submit");
        Assert.assertTrue(el("login-error").getText().contains("Invalid username"));
        Assert.assertTrue(driver.getCurrentUrl().endsWith("/student/login"));
    }
    @Test(description = "TC06: Invalid credentials show an informative error")
    public void invalidLoginIsRejected() {
        driver.get(baseUrl + "/admin/login");
        type("login-username", "admin");
        type("login-password", "wrong-password");
        click("login-submit");
        Assert.assertTrue(el("login-error").getText().contains("Invalid username"));
    }
}
