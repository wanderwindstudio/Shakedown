Shader "Shakedown/Spike/Faceted clouds"
{
    SubShader
    {
        Tags { "RenderPipeline"="UniversalPipeline" "Queue"="Transparent" }
        Pass
        {
            Blend SrcAlpha OneMinusSrcAlpha
            ZWrite Off
            HLSLPROGRAM
            #pragma vertex Vert
            #pragma fragment Frag
            #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Lighting.hlsl"
            struct Input { float4 position:POSITION; float3 normal:NORMAL; half4 colour:COLOR; };
            struct Varying { float4 position:SV_POSITION; half3 normal:TEXCOORD0; half4 colour:COLOR; };
            Varying Vert(Input v) { Varying o; o.position=TransformObjectToHClip(v.position.xyz); o.normal=TransformObjectToWorldNormal(v.normal); o.colour=v.colour; return o; }
            half4 Frag(Varying i):SV_Target
            {
                Light sun=GetMainLight(); half d=dot(normalize(i.normal),sun.direction);
                half3 light=lerp(half3(.005,.007,.01),sun.color*max(.18,d),smoothstep(-.01,.01,d));
                return half4(i.colour.rgb*light,i.colour.a);
            }
            ENDHLSL
        }
    }
}
