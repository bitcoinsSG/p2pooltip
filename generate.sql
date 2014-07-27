	

    CREATE DATABASE p2pooltip;
     
    USE p2pooltip;
     
    CREATE TABLE IF NOT EXISTS `tips` (
            `id` BIGINT NOT NULL AUTO_INCREMENT,                                            -- index
            `commentid` VARCHAR(10) NOT NULL,                                                       -- Reddit comment id of tip
            `messageid` VARCHAR(10) NOT NULL,                                                       -- Reddit message id of Changetip message
            `amount` BIGINT NOT NULL,                                                                       -- original tip amount, in satoshis
            `sent` BIGINT NOT NULL,                                                                         -- final tip amount after fees, in satoshis
            `username` VARCHAR(20) NOT NULL,                                                        -- Reddit username of tipper
            `time` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,            -- timestamp
            `txid` VARCHAR(64) NOT NULL,                                                            -- Bitcoin transaction id
            PRIMARY KEY (`id`),
            KEY `commentid` (`commentid`)
    ) ENGINE=InnoDB DEFAULT CHARSET=latin1 AUTO_INCREMENT=1;

