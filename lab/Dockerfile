FROM mcr.microsoft.com/dotnet/sdk:6.0 AS build
WORKDIR /src

COPY vulnerable.csproj ./
RUN dotnet restore vulnerable.csproj

COPY mock_vulnerable_app.cs ./
RUN dotnet publish vulnerable.csproj -c Release -o /out /p:UseAppHost=false

FROM mcr.microsoft.com/dotnet/aspnet:6.0
WORKDIR /app

RUN addgroup --system appgroup \
	&& adduser --system --ingroup appgroup --uid 10001 appuser

COPY --from=build /out ./

USER appuser
EXPOSE 80
CMD ["dotnet", "vulnerable.dll", "--urls", "http://0.0.0.0:80"]