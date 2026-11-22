/*
 * Laner Money — money parsing. See include/money.h for the contract.
 */
#include "money.h"

#include <stddef.h>   /* NULL */

/* Plain ASCII range check rather than isdigit(): isdigit is
 * locale-dependent, and passing it a negative char (any byte >= 0x80 on
 * platforms where char is signed, e.g. the 0xA3 in a Latin-1 '£') is
 * undefined behaviour. */
static int is_ascii_digit(char c)
{
    return c >= '0' && c <= '9';
}

int parse_pence(const char *s, int64_t *out)
{
    if (s == NULL || out == NULL) {
        return -1;
    }

    /* Whole pounds: at least one digit. The limit is checked on every
     * digit, so pounds never exceeds LANER_MAX_PENCE / 100 and
     * pounds * 10 + 9 can't come close to overflowing int64_t, however
     * long the input is. */
    int64_t pounds = 0;
    const char *p = s;
    if (!is_ascii_digit(*p)) {
        return -1;                      /* "", ".5", "-5", " 12", "£5" */
    }
    while (is_ascii_digit(*p)) {
        pounds = pounds * 10 + (*p - '0');
        if (pounds > LANER_MAX_PENCE / 100) {
            return -1;                  /* too large; stop before overflow */
        }
        p++;
    }

    /* Optional fraction: '.' then exactly one or two digits. */
    int64_t frac = 0;
    if (*p == '.') {
        p++;
        if (!is_ascii_digit(*p)) {
            return -1;                  /* "12." */
        }
        frac = (*p - '0') * 10;         /* "12.3" means 30p, not 3p */
        p++;
        if (is_ascii_digit(*p)) {
            frac += *p - '0';
            p++;
        }
    }

    /* Anything left over is an error: "12.345", "12 ", "12abc", "1,000". */
    if (*p != '\0') {
        return -1;
    }

    int64_t total = pounds * 100 + frac;
    if (total > LANER_MAX_PENCE) {
        return -1;                      /* "1000000.01" */
    }

    *out = total;                       /* only written on success */
    return 0;
}
