/*
 * Laner Money — entry point.
 *
 * Fresh-start scaffold: proves the toolchain end to end by opening (or
 * creating) the SQLite database and closing it cleanly. No schema, no
 * queries yet — that's M1.
 */

#include <stdio.h>     /* printf, fprintf */
#include <stdlib.h>    /* EXIT_SUCCESS, EXIT_FAILURE */
#include <sys/stat.h>  /* umask — POSIX, fine for a Linux-first project */

#include <sqlite3.h>

/* Injected by CMake (target_compile_definitions). The fallback keeps the
 * file compilable outside CMake, e.g. a quick one-off gcc command. */
#ifndef LANER_VERSION
#define LANER_VERSION "unknown"
#endif

/*
 * Relative to the current working directory, so run from the repo root:
 *   ./build/laner
 * Deployment (M-later) will make this configurable; hardcoding is fine
 * for a scaffold but would be wrong for a service.
 */
static const char DB_PATH[] = "data/laner.db";

int main(void)
{
    /*
     * File permissions. When SQLite creates a new database file it asks
     * for mode 0644 (owner rw, everyone else read); the kernel then
     * removes any bits set in the process umask. The usual umask (022)
     * leaves 0644 — so any user on the machine could read your finances.
     * umask(077) removes all group/other bits, giving 0600 (owner only).
     * This also covers the -journal/-wal files SQLite creates later.
     * umask() can't fail, so there's no return value to check — the value
     * it returns is the *previous* mask, which we don't need.
     */
    (void)umask(077);

    sqlite3 *db = NULL;

    /*
     * sqlite3_open_v2 instead of sqlite3_open, so the behaviour is stated
     * explicitly rather than relying on defaults:
     *   READWRITE | CREATE  — open for writing, create if missing
     *   NOFOLLOW            — refuse if the path is a symlink. Stops a
     *                         planted symlink (data/laner.db -> somewhere
     *                         else) redirecting writes. Needs SQLite 3.31+.
     * Last argument NULL = default VFS (the OS file layer).
     */
    const int flags = SQLITE_OPEN_READWRITE | SQLITE_OPEN_CREATE |
                      SQLITE_OPEN_NOFOLLOW;
    int rc = sqlite3_open_v2(DB_PATH, &db, flags, NULL);

    if (rc != SQLITE_OK) {
        /*
         * Gotcha: even on failure SQLite usually allocates a handle and
         * stores it in db, purely so you can read the error message. That
         * handle must still be closed or it leaks. If allocation itself
         * failed, db is NULL — so fall back to sqlite3_errstr(rc), which
         * needs no handle. sqlite3_close(NULL) is a documented no-op.
         *
         * Errors go to stderr: stdout is for real output (later, `laner
         * list`), and mixing the two breaks anything piping it.
         */
        fprintf(stderr, "laner: cannot open database '%s': %s\n", DB_PATH,
                db ? sqlite3_errmsg(db) : sqlite3_errstr(rc));
        sqlite3_close(db);
        return EXIT_FAILURE;
    }

    /*
     * sqlite3_libversion() is the library actually loaded at runtime;
     * SQLITE_VERSION is the header we compiled against. They can differ
     * if the system library is upgraded later, so print both.
     */
    printf("Laner Money %s\n", LANER_VERSION);
    printf("SQLite runtime %s (built against %s)\n",
           sqlite3_libversion(), SQLITE_VERSION);
    printf("Opened database: %s\n", DB_PATH);

    /*
     * Close and *check* it. sqlite3_close returns SQLITE_BUSY if prepared
     * statements are still open — always a bug in our code (a statement
     * not finalized). Ignoring it would hide that bug and leak memory.
     */
    rc = sqlite3_close(db);
    if (rc != SQLITE_OK) {
        fprintf(stderr, "laner: error closing database: %s\n",
                sqlite3_errstr(rc));
        return EXIT_FAILURE;
    }

    /*
     * printf can fail (stdout redirected to a full disk, or a pipe whose
     * reader has gone away) and output is buffered, so the failure may
     * only surface at flush. Rather than checking every printf, flush
     * once and check the stream's sticky error flag. Without this,
     * `laner list > backup.txt` could "succeed" with a truncated file.
     * (stderr is unbuffered and is our last resort, so its fprintf
     * results aren't checked — there's nowhere left to report to.)
     */
    if (fflush(stdout) != 0 || ferror(stdout)) {
        fprintf(stderr, "laner: error writing output\n");
        return EXIT_FAILURE;
    }

    return EXIT_SUCCESS;
}
