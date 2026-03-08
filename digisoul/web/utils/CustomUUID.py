from django.db.models import CharField
import shortuuid

# custome uuid field
class UUIDField(CharField):
    def __init__(self, auto=True, *args, **kwargs):
        self.auto = auto
        self.prefix = kwargs.pop('prefix', '')
        self.length = kwargs.pop('length', 32)
        if auto:
            # 如果uuid是自动生成的，则不要让用户编辑
            kwargs['editable'] = False
            kwargs['blank'] = False
        super().__init__(*args, **kwargs)

    def pre_save(self, model_instance, add):
        value = super(UUIDField, self).pre_save(model_instance, add)
        if self.auto and not value:
            value = shortuuid.uuid()
            # 处理长度限制
            if self.length:
                value = value[:self.length]
            # 添加前缀
            if self.prefix:
                value = f"{self.prefix}_{value}"
            setattr(model_instance, self.attname, value)
        return value