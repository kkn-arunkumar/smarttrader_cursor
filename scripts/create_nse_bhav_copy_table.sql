-- NSE Bhav Copy table for equity EOD data from www.nseindia.com
-- Run this in Oracle if you prefer to create the table manually.

CREATE TABLE NSE_BHAV_COPY (
    SYMBOL         VARCHAR2(50),
    SERIES         VARCHAR2(10),
    OPEN           NUMBER(20,4),
    HIGH           NUMBER(20,4),
    LOW            NUMBER(20,4),
    CLOSE          NUMBER(20,4),
    LAST           NUMBER(20,4),
    PREVCLOSE      NUMBER(20,4),
    TOTTRDQTY      NUMBER(20),
    TOTTRDVAL      NUMBER(20,4),
    TIMESTAMP      DATE,
    TOTALTRADES    NUMBER(20),
    ISIN           VARCHAR2(20),
    LOAD_DATE      DATE DEFAULT SYSDATE,
    CONSTRAINT NSE_BHAV_COPY_PK PRIMARY KEY (SYMBOL, SERIES, TIMESTAMP)
);

CREATE INDEX NSE_BHAV_COPY_TS ON NSE_BHAV_COPY (TIMESTAMP);
CREATE INDEX NSE_BHAV_COPY_SYMBOL ON NSE_BHAV_COPY (SYMBOL);
