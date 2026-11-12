# HTTPS access instructions used an IP with only a Host header

Remote custom-domain TLS validates the service hostname. Printing HTTPS URLs by
LoadBalancer IP plus a Host header does not select that TLS server name and can
fail hostname verification when the IP is not a certificate SAN.

Print named service HTTPS URLs and DNS/curl --resolve guidance with an explicit
public CA. HTTP Host-header examples remain valid. Actual remote GitHub, Jira,
dashboard and MLflow HTTPS routes pass with CA verification enabled; dashboard
service links contain the custom domain and no default-domain service links.
Shell syntax and whitespace checks pass.
