FROM eclipse-temurin:8-jdk

WORKDIR /workspace

COPY source/ .

RUN sed -i 's/\r$//' mvnw \
    && chmod +x mvnw \
    && ./mvnw clean install -DskipTests

WORKDIR /workspace/site

EXPOSE 8080

ENTRYPOINT ["../mvnw", "spring-boot:run", "-DskipTests"]