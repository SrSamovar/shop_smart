from drf_spectacular.utils import OpenApiExample, OpenApiParameter

email_param = OpenApiParameter(
    name='email',
    type=str,
    location=OpenApiParameter.QUERY,
    description='Email адрес пользователя',
    required=False,
)

token_param = OpenApiParameter(
    name='token',
    type=str,
    location=OpenApiParameter.QUERY,
    description='Токен подтверждения email',
    required=False,
)

password_param = OpenApiParameter(
    name='password',
    type=str,
    location=OpenApiParameter.QUERY,
    description='Пароль пользователя',
    required=False,
)

type_param = OpenApiParameter(
    name='type',
    type=str,
    location=OpenApiParameter.QUERY,
    description='Тип пользователя',
    required=False,
)

first_name_param = OpenApiParameter(
    name='first_name',
    type=str,
    location=OpenApiParameter.QUERY,
    description='Имя пользователя',
    required=False,
)

last_name_param = OpenApiParameter(
    name='last_name',
    type=str,
    location=OpenApiParameter.QUERY,
    description='Фамилия пользователя',
    required=False,
)

city_param = OpenApiParameter(
    name='city',
    type=str,
    location=OpenApiParameter.QUERY,
    description='Город пользователя',
    required=False,
)

phone_param = OpenApiParameter(
    name='phone',
    type=str,
    location=OpenApiParameter.QUERY,
    description='Телефон пользователя',
    required=False,
)

street_param = OpenApiParameter(
    name='street',
    type=str,
    location=OpenApiParameter.QUERY,
    description='Улица пользователя',
    required=False,
)

house_number_param = OpenApiParameter(
    name='house_number',
    type=int,
    location=OpenApiParameter.QUERY,
    description='Номер дома пользователя',
    required=False,
)

flat_number_param = OpenApiParameter(
    name='flat_number',
    type=int,
    location=OpenApiParameter.QUERY,
    description='Номер квартиры пользователя',
    required=False,
)
