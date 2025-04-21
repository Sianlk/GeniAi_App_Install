# AI Content Creation Module
import ai_image_generator
import social_media_api

def generate_viral_content(trend_data):
    print("[INFO] Generating viral content based on trends...")
    content = ai_image_generator.create_viral_image(trend_data)
    print("[DEBUG] Viral content generated.")
    return content

def post_content_to_platform(content, platform):
    print(f"[INFO] Posting content to {platform}...")
    social_media_api.post(platform, content)
