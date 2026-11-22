/*
 * Laner Money — money parsing.
 *
 * Amounts are stored as whole pence in an int64_t, never as floating
 * point: 0.1 + 0.2 != 0.3 in binary floating point, and that kind of
 * rounding drift is unacceptable for a ledger.
 */
#ifndef LANER_MONEY_H
#define LANER_MONEY_H

#include <stdint.h>   /* int64_t, INT64_C */

/* Largest amount parse_pence accepts: £1,000,000.00. Far below INT64_MAX,
 * so any arithmetic on two accepted amounts can't overflow. */
#define LANER_MAX_PENCE INT64_C(100000000)

/*
 * Parse a non-negative pounds amount into pence.
 *
 * Accepted:  one or more ASCII digits, optionally followed by '.' and
 *            exactly one or two digits ("12", "12.3", "12.34").
 * Rejected:  NULL, "", signs, whitespace, '£', commas, exponents,
 *            "12." / ".5", more than two decimals, anything above
 *            LANER_MAX_PENCE.
 *
 * Returns 0 and writes the result to *out on success.
 * Returns -1 on any failure and leaves *out untouched.
 */
int parse_pence(const char *s, int64_t *out);

#endif /* LANER_MONEY_H */
