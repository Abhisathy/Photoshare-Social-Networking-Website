#CREATE DATABASE photoshare;
#USE photoshare;

#CREATE TABLE Users (
#    user_id int  AUTO_INCREMENT,
#    email varchar(255) UNIQUE,
#    password varchar(255),
#  CONSTRAINT users_pk PRIMARY KEY (user_id)
#);

#CREATE TABLE Pictures
#(
#  picture_id int  AUTO_INCREMENT,
#  user_id int,
#  imgdata longblob ,
#  caption VARCHAR(255),
#  INDEX upid_idx (user_id),
#  CONSTRAINT pictures_pk PRIMARY KEY (picture_id)
#);
#INSERT INTO Users (email, password) VALUES ('test@bu.edu', 'test');
#INSERT INTO Users (email, password) VALUES ('test1@bu.edu', 'test');
CREATE DATABASE photoshare;
USE photoshare;

CREATE TABLE Users (
    users_id INT NOT NULL AUTO_INCREMENT,
    gender VARCHAR(6),
    email VARCHAR(255) UNIQUE,
    password VARCHAR(255) NOT NULL,
    dob DATE,
    city VARCHAR(40),
    f_name VARCHAR(40),
    l_name VARCHAR(40),
    PRIMARY KEY (users_id)
);

CREATE TABLE Friendship(
	users_id1 INT NOT NULL,
	users_id2 INT NOT NULL,
	PRIMARY KEY(users_id1, users_id2),
	FOREIGN KEY (users_id1) REFERENCES Users(users_id) ON DELETE CASCADE,
	FOREIGN KEY (users_id2) REFERENCES Users(users_id) ON DELETE CASCADE
);

CREATE TABLE Album (
  a_id       INT         NOT NULL AUTO_INCREMENT,
  a_name     VARCHAR(40) NOT NULL,
  #DOC TIMESTAMP NOT NULL,
  users_id   INT NOT NULL,
  PRIMARY KEY (a_id),
  FOREIGN KEY (users_id) REFERENCES Users (users_id) ON DELETE CASCADE
  #FOREIGN KEY (picture_id) REFERENCES Pictures(picture_id) ON DELETE CASCADE
);

CREATE TABLE Pictures(
	picture_id INT NOT NULL AUTO_INCREMENT,
  users_id INT NOT NULL,
	caption VARCHAR(255),
	imgdata VARCHAR(255) NOT NULL,
  #INDEX upicture_id_idx (users_id),
	#a_id INT NOT NULL DEFAULT 0,
	PRIMARY KEY (picture_id)
	#FOREIGN KEY (a_id) REFERENCES ALBUM(a_id) ON DELETE CASCADE
);

create table APassoc(
	a_id INT NOT NULL,
	picture_id INT NOT NULL,
	foreign key(a_id) references Album(a_id) on delete cascade,
	foreign key(picture_id) references Pictures(picture_id) on delete cascade,
	PRIMARY KEY (a_id,picture_id)
);


CREATE TABLE Comment (
	c_id INT NOT NULL AUTO_INCREMENT,
	content VARCHAR(200) NOT NULL,
	DOC TIMESTAMP NOT NULL,
	users_id INT NOT NULL,
	picture_id INT NOT NULL,
	PRIMARY KEY (c_id),
	FOREIGN KEY (users_id) REFERENCES Users(users_id) ON DELETE CASCADE,
	FOREIGN KEY (picture_id) REFERENCES Pictures(picture_id) ON DELETE CASCADE
);

CREATE TABLE Liketable(
	users_id INT NOT NULL,
	picture_id INT NOT NULL,
	DOC TIMESTAMP NOT NULL,
        PRIMARY KEY (users_id, picture_id),
	FOREIGN KEY (users_id) REFERENCES Users(users_id) ON DELETE CASCADE,
	FOREIGN KEY (picture_id) REFERENCES Pictures(picture_id) ON DELETE CASCADE
);

CREATE TABLE ASSOCIATE(
	picture_id INT NOT NULL,
	Hashtag VARCHAR(40) NOT NULL,
	FOREIGN KEY (picture_id) REFERENCES Pictures(picture_id) ON DELETE CASCADE,
	PRIMARY KEY (picture_id, Hashtag)
);
