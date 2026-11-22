/* Unit tests for parse_pence. Exits non-zero if any case fails, so
 * CTest (see CMakeLists.txt) can run it. */
#include "money.h"

#include <stdio.h>
#include <stdlib.h>

static int failures = 0;

static void expect_ok(const char *in, int64_t want)
{
    int64_t got = -999;
    int rc = parse_pence(in, &got);
    if (rc != 0 || got != want) {
        printf("FAIL  \"%s\": expected %lld, got rc=%d value=%lld\n",
               in, (long long)want, rc, (long long)got);
        failures++;
    } else {
        printf("ok    \"%s\" -> %lld\n", in, (long long)got);
    }
}

static void expect_reject(const char *in)
{
    int64_t got = -999;                 /* sentinel: must stay unchanged */
    int rc = parse_pence(in, &got);
    if (rc != -1 || got != -999) {
        printf("FAIL  \"%s\": expected reject, got rc=%d value=%lld\n",
               in ? in : "(NULL)", rc, (long long)got);
        failures++;
    } else {
        printf("ok    \"%s\" rejected\n", in ? in : "(NULL)");
    }
}

int main(void)
{
    expect_ok("12", 1200);
    expect_ok("12.3", 1230);
    expect_ok("12.34", 1234);
    expect_ok("0.05", 5);
    expect_ok("0", 0);
    expect_ok("1000000", 100000000);
    expect_ok("1000000.00", 100000000);

    expect_reject(NULL);
    expect_reject("");
    expect_reject("-5");
    expect_reject("12.345");
    expect_reject("12.");
    expect_reject(".5");
    expect_reject(" 12");
    expect_reject("12 ");
    expect_reject("12abc");
    expect_reject("1,000");
    expect_reject("1e3");
    expect_reject("1000000.01");
    expect_reject("1000001");
    expect_reject("99999999999999999999999");   /* would overflow int64 */
    expect_reject("\xa3" "5");                  /* "£5" as a raw byte */

    /* NULL out pointer must be rejected, not crash. */
    if (parse_pence("5", NULL) != -1) {
        printf("FAIL  NULL out pointer accepted\n");
        failures++;
    } else {
        printf("ok    NULL out pointer rejected\n");
    }

    printf("\n%s (%d failure%s)\n", failures ? "FAILED" : "ALL PASSED",
           failures, failures == 1 ? "" : "s");
    return failures ? EXIT_FAILURE : EXIT_SUCCESS;
}