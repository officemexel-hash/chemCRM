from app.messaging.messengers.whatsapp_business import WhatsAppBusinessConnector


class ThreemaGatewayConnector(WhatsAppBusinessConnector):
    compliance = WhatsAppBusinessConnector.compliance
