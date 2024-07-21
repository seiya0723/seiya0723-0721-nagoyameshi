from django.db import models
from django.conf import settings
from django.utils import timezone
from django.core.validators import RegexValidator
from django.contrib.auth import get_user_model
User = get_user_model()
from django.core.validators import MinValueValidator,MaxValueValidator
from django.core.exceptions import ValidationError
from datetime import datetime, timedelta
from django.db.models import Avg

# models.Modelを継承した汎用クラス
class ExtendedModel(models.Model):
    deleted_at = models.DateTimeField(verbose_name='論理削除日', auto_now=True, blank=True, null=True)
    updated_at = models.DateTimeField(verbose_name='更新日', auto_now=True, blank=True, null=True)
    created_at = models.DateTimeField(verbose_name='作成日', auto_now_add=True)

# カテゴリー
class Category(ExtendedModel):
    name = models.CharField(verbose_name='カテゴリ名', max_length=15)

    def __str__(self):
        return self.name

# 曜日　整数値は月曜日か0で日曜日が6。
class Day(models.Model):
    name = models.CharField(verbose_name='曜日', max_length=10)
    key = models.PositiveIntegerField(verbose_name='整数値', default=0)

    def __str__(self):
        return self.name
    

# 店舗
def get_top_image_path(instance, filename):
    return "nagoyameshi/restaurant/%s/top/%s"%(str(instance.pk), filename)

class Restaurant(ExtendedModel):
    name = models.CharField(verbose_name='店舗名', max_length=30)
    category_id = models.ForeignKey(Category, verbose_name='カテゴリー', on_delete=models.PROTECT)
    description = models.CharField(verbose_name='店舗説明', max_length=500)
    image = models.ImageField(verbose_name='トップ画像', upload_to=get_top_image_path, 	blank=True, default='nagoyameshi/noimage.png')
    floor_price = models.PositiveIntegerField(verbose_name='下限価格')
    maximum_price = models.PositiveIntegerField(verbose_name='上限価格')
    opening_time = models.TimeField(verbose_name='開店時刻')
    closing_time = models.TimeField(verbose_name='閉店時刻')

    postal_code_regex = RegexValidator(regex=r'^[0-9]{3}-[0-9]{4}$')
    postal_code = models.CharField(verbose_name='郵便番号', max_length=8, validators=[postal_code_regex])

    city = models.CharField(verbose_name='市区町村', max_length=50)
    street_address = models.CharField(verbose_name='番地以降住所', max_length=50)

    phone_number_regex = RegexValidator(regex=r'^[0-9]{10,11}$')
    phone_number = models.CharField(verbose_name='電話番号', max_length=11, validators=[phone_number_regex])

    regular_closing_day = models.ManyToManyField(Day, verbose_name='定休日')

    def __str__(self):
        return self.name
    
    def get_regular_closing_day(self):
        return "\n".join([day.name for day in self.regular_closing_day.all()])
    
    def count_reviews(self):
        return Review.objects.filter(restaurant_id=self.id).count()

    def stars_avg_str(self):
        '''
        星の数の平均値を文字列の長さに変換するメソッド
        '''
        reviews = Review.objects.filter(restaurant_id=self.id).aggregate(Avg("number_of_stars"))
        avg     = reviews["number_of_stars__avg"]

        if not avg:
            avg = 0
        
        true_num = int(avg)
        half_num = 0
        false_num = int( MAX_STAR - avg )

        few = avg - true_num

        if few == 0:
            pass
        elif 0 < few < 0.4 :
            false_num += 1
        elif 0.4 <= few < 0.6:
            half_num += 1
        else:
            true_num += 1
        
        avg = round(avg, 2)

        true_star = true_num * ' '
        half_star = half_num * ' '
        false_star = false_num * ' '
        return {'num':avg, 'true_star': true_star, 'half_star': half_star, 'false_star': false_star}
        
        
    def number_of_stars_str(self):
        '''
        星の数分の長さの文字列を返すメソッド
        '''
        true_star = self.number_of_stars * ' '
        false_star = (MAX_STAR - self.number_of_stars) * ' '
        return {'true_star': true_star, 'false_star': false_star}
    
# 店舗写真（詳細）
def get_photos_path(instance, filename):
    return "nagoyameshi/restaurant/%s/photos/%s"%(str(instance.restaurant_id.pk), filename)

class RestaurantPhoto(ExtendedModel):
    restaurant_id = models.ForeignKey(Restaurant, verbose_name='店舗', on_delete=models.CASCADE)
    image = models.ImageField(verbose_name='画像', upload_to=get_photos_path)

# レビュー
MAX_STAR = 5
class Review(ExtendedModel):
    restaurant_id = models.ForeignKey(Restaurant, verbose_name='店舗', on_delete=models.CASCADE)
    user_id = models.ForeignKey(settings.AUTH_USER_MODEL, verbose_name="ユーザー", on_delete=models.CASCADE)
    number_of_stars = models.PositiveIntegerField(verbose_name='星の数', validators=[MinValueValidator(1),MaxValueValidator(MAX_STAR)],default=1)
    comment = models.CharField(verbose_name='コメント', max_length=800)
    visited_date = models.DateField(verbose_name='利用日')

    def number_of_stars_str(self):
        '''
        星の数分の長さの文字列を返すメソッド
        '''
        true_star = self.number_of_stars * ' '
        false_star = (MAX_STAR - self.number_of_stars) * ' '
        return {'true_star': true_star, 'false_star': false_star}
    
    def clean(self):
        '''
        バリデーション
        '''
        super().clean()
        today = timezone.now().date()
        if self.visited_date > today:
            raise ValidationError("利用日には過去の日付を選択してください。")

# お気に入り
class Favorite(models.Model):
    class Meta:
        unique_together=("user_id","restaurant_id")

    restaurant_id = models.ForeignKey(Restaurant, verbose_name='店舗', on_delete=models.CASCADE)
    user_id = models.ForeignKey(settings.AUTH_USER_MODEL, verbose_name="ユーザー", on_delete=models.CASCADE)


# 予約
class Reservation(ExtendedModel):
    user_id = models.ForeignKey(settings.AUTH_USER_MODEL, verbose_name="ユーザー", on_delete=models.CASCADE)
    restaurant_id = models.ForeignKey(Restaurant, verbose_name='店舗', on_delete=models.CASCADE)
    reservation_datetime = models.DateTimeField(verbose_name='予約日時')
    number_of_persons = models.PositiveIntegerField(verbose_name='予約人数')
    comment = models.CharField(verbose_name='コメント', max_length=200, null=True, blank=True)

    def clean(self):
        '''
        バリデーション
        '''
        super().clean()

        # 予約日時が過去の場合エラーを返す
        if self.reservation_datetime < timezone.now():
            raise ValidationError('予約日には未来の日付を選択してください。')
        
        # 営業時間外の予約の場合エラーを返す
        restaurant = self.restaurant_id
        reservation_datetime = self.reservation_datetime.time()
        if  not restaurant.opening_time <= reservation_datetime < restaurant.closing_time:
            raise ValidationError('予約時刻は営業時間内で指定してください。')
        
        # 定休日の予約の場合エラーを返す
        weekday = self.reservation_datetime.weekday()
        if restaurant.regular_closing_day.filter(key=weekday).exists():
            raise ValidationError('定休日に予約することはできません。別の曜日を選択してください。')
        
        # 前後2時間に別の店舗を予約している場合エラーを返す
        start = self.reservation_datetime - timedelta(hours=2)
        end = self.reservation_datetime + timedelta(hours=2)
        if Reservation.objects.filter(reservation_datetime__gte=start, reservation_datetime__lte=end).exists():
            raise ValidationError('指定された日時の前後2時間に別の店舗を予約済みのため、予約することができません。')



