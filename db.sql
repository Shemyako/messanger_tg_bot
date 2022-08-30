CREATE TABLE "users" (
	"id" serial NOT NULL,
	"name" varchar(255) NOT NULL UNIQUE,
	"password" varchar(255) NOT NULL,
	CONSTRAINT "users_pk" PRIMARY KEY ("id")
) WITH (
  OIDS=FALSE
);



CREATE TABLE "messages" (
	"id" serial NOT NULL,
	"from_user" int NOT NULL,
	"to_user" int NOT NULL,
	"text" varchar(50) NOT NULL,
	"is_readed" bool NOT NULL,
	CONSTRAINT "messages_pk" PRIMARY KEY ("id")
) WITH (
  OIDS=FALSE
);




ALTER TABLE "messages" ADD CONSTRAINT "messages_fk0" FOREIGN KEY ("from_user") REFERENCES "users"("id");
ALTER TABLE "messages" ADD CONSTRAINT "messages_fk1" FOREIGN KEY ("to_user") REFERENCES "users"("id");


