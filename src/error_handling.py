"""
Error handling utilities for Antibiotic Resistance Gene Detector.

This module provides custom exception types used across the project and a
small utility to produce a minimal error report when a sample cannot be
processed (for example when a database is missing or corrupted).

Classes
-------
MissingFileError
    Raised when an expected file is not found on disk.
CorruptedInputError
    Raised when a FASTA file cannot be parsed or appears corrupted.
NoHitsFoundError
    Raised when no resistance gene hits are found for a sample.

Functions
---------
safe_fail
    Write a minimal error CSV and log the error message.
"""

class MissingFileError(Exception):
    """Raised when an expected file is missing."""
    pass

class CorruptedInputError(Exception):
    """Raised when input FASTA is corrupted or invalid."""
    pass

class NoHitsFoundError(Exception):
    """Raised when no resistance genes are detected."""
    pass

def safe_fail(message, output_path="output/results.csv"):
    """
    Write a minimal error report and log the error.

    This helper is used when a sample cannot be processed due to a
    recoverable problem (for example a missing database). It writes a
    two-line CSV file with an "error" header followed by the message and
    emits an error-level log entry so CI and users can diagnose the cause.

    Parameters
    ----------
    message : str
        Human-readable error message to write to the CSV and the log.
    output_path : str, optional
        Path to the CSV file to write (default: ``output/results.csv``).

    Returns
    -------
    None

    Notes
    -----
    This function intentionally keeps output minimal so downstream
    consumers can detect error cases programmatically.
    """
    import logging
    logging.error(message)
    with open(output_path, "w") as f:
        f.write("error\n" + message + "\n")
