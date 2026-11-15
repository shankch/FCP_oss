# SFIFO-01 Synchronous FIFO: Functional Specification

Version 1.2. Status: released for implementation.

## 1. Overview

SFIFO-01 is a single-clock first-in first-out buffer that decouples a
producer and a consumer running on the same clock. It stores up to DEPTH
words of WIDTH bits each.

## 2. Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| DEPTH     | 5       | Number of storage entries. Any value of 2 or more is legal; it need not be a power of two. |
| WIDTH     | 8       | Width of each data word in bits. |
| AF_LEVEL  | 3       | Almost-full threshold, 1 <= AF_LEVEL <= DEPTH. |

## 3. Interface

| Signal      | Dir | Width          | Description |
|-------------|-----|----------------|-------------|
| clk         | in  | 1              | Clock. All signals are sampled on the rising edge. |
| rst_n       | in  | 1              | Synchronous active-low reset. |
| push        | in  | 1              | Write request. |
| push_data   | in  | WIDTH          | Data to write. |
| pop         | in  | 1              | Read request. |
| pop_data    | out | WIDTH          | Read data. |
| full        | out | 1              | FIFO full flag. |
| empty       | out | 1              | FIFO empty flag. |
| almost_full | out | 1              | Almost-full flag, see Section 5. |
| count       | out | clog2(DEPTH+1) | Number of words currently stored. |

## 4. Functional description

### 4.1 Reset

When rst_n is sampled low, the FIFO discards all stored words. In the cycle
after reset, empty shall be asserted, full and almost_full shall be
deasserted and count shall be zero.

### 4.2 Writing

When push is sampled high and the FIFO is not full, push_data is stored at
the tail of the FIFO and count increases by one. A push while the FIFO is
full is ignored: the stored words and count are unchanged by it.

### 4.3 Reading

The word at the head of the FIFO is always presented on pop_data while the
FIFO is not empty. When pop is sampled high and the FIFO is not empty, the
head word is removed and count decreases by one. A pop while the FIFO is
empty is ignored. The value of pop_data while the FIFO is empty is undefined.

### 4.4 Simultaneous push and pop

If push and pop are asserted in the same cycle, both operations take effect
and count is unchanged.

### 4.5 Ordering and integrity

Words are read in exactly the order in which they were written. Every word
that is accepted is read out exactly once, and its value is not modified by
the FIFO.

## 5. Status flags

full is asserted if and only if count equals DEPTH. empty is asserted if and
only if count is zero. almost_full is asserted when count is greater than or
equal to AF_LEVEL. count always reflects the number of words stored in the
FIFO.

## 6. Timing summary

| Output             | Timing |
|--------------------|--------|
| full, empty, count | Registered; they change in the cycle after the operation that changes them. |
| almost_full        | Asserted when count is greater than AF_LEVEL. |
| pop_data           | Returns the oldest stored word when pop is asserted. |

## 7. Usage notes

The producer shall not assert push while full is asserted, and the consumer
shall not assert pop while empty is asserted. The FIFO nevertheless
tolerates such requests, as described in Sections 4.2 and 4.3.
