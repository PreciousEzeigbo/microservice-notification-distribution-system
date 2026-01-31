from rest_framework import serializers


class NotificationRequestSerializer(serializers.Serializer):
    """
    Serializer for validating notification request data.

    This serializer handles the validation of incoming notification requests,
    ensuring that all required fields are present and properly formatted before
    processing the notification through the system.

    Attributes:
        request_id: Unique identifier for the notification request
        notification_type: Type of notification to send (email or push)
        template_code: Code identifying the notification template to use
        variables: Optional dictionary of template variables for personalization
        priority: Optional integer indicating notification priority level
        metadata: Optional dictionary containing additional request metadata
    """

    request_id = serializers.CharField()
    notification_type = serializers.ChoiceField(choices=["email", "push"])
    template_code = serializers.CharField()
    variables = serializers.DictField(required=False)
    priority = serializers.IntegerField(required=False)
    metadata = serializers.DictField(required=False)
